#!/usr/bin/env python
# -*- coding: utf-8 -*-

from trytond.model import ModelView, ModelSQL, fields
from trytond.pool import Pool
from trytond.pyson import Eval, Bool
from trytond.exceptions import UserWarning
from datetime import datetime

__all__ = ['GnuHealthLabImmunoassay', 'GnuHealthLabImmunoassayAntibody']


class GnuHealthLabImmunoassay(ModelSQL, ModelView):
    'Lab Immunoassay Process'
    __name__ = 'gnuhealth.lab.immunoassay'
    
    # Relación con la muestra del workflow
    workflow_sample = fields.Many2One('gnuhealth.lab.workflow.sample', 
        'Workflow Sample', required=True, ondelete='CASCADE',
        domain=[('state', 'in', ['received', 'processing'])],
        help='Sample being processed in immunoassay')
    
    # Información básica (campos función desde workflow_sample)
    name = fields.Function(fields.Char('Order Number'), 'get_sample_info')
    patient = fields.Function(fields.Many2One('gnuhealth.patient', 'Patient'), 
        'get_sample_info')
    sample_type = fields.Function(fields.Char('Sample Type'), 'get_sample_info')
    
    # Tipo de inmunoensayo
    assay_type = fields.Selection([
        ('elisa', 'ELISA (Enzyme-Linked Immunosorbent Assay)'),
        ('clia', 'CLIA (Chemiluminescent Immunoassay)'),
    ], 'Assay Type', required=True,
    help='Type of immunoassay')
    
    # Kit utilizado
    kit_name = fields.Char('Kit Name', required=True,
        help='Commercial kit name and manufacturer')
    
    kit_lot = fields.Char('Kit Lot Number',
        help='Lot number of the kit used')
    
    kit_expiry = fields.Date('Kit Expiry Date',
        help='Expiration date of the kit')
    
    # Fechas del proceso
    processing_date = fields.DateTime('Processing Date')
    
    delivery_date = fields.DateTime('Delivery Date')
    
    # Profesional responsable
    responsible_professional = fields.Many2One('gnuhealth.healthprofessional',
        'Responsible Professional', required=True,
        help='Professional responsible for the complete process')
    
    # Anticuerpos/Antígenos testeados
    antibodies = fields.One2Many('gnuhealth.lab.immunoassay.antibody', 
        'immunoassay', 'Antibodies/Antigens',
        help='List of antibodies or antigens tested')
    
    # Control de calidad
    positive_control = fields.Selection([
        (None, ''),
        ('pass', 'Pass'),
        ('fail', 'Fail'),
        ('not_done', 'Not Done'),
    ], 'Positive Control')
    
    negative_control = fields.Selection([
        (None, ''),
        ('pass', 'Pass'),
        ('fail', 'Fail'),
        ('not_done', 'Not Done'),
    ], 'Negative Control')
    
    # Estado del proceso
    state = fields.Selection([
        ('draft', 'Draft'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ], 'State', readonly=True, required=True)
    
    # Observaciones
    observations = fields.Text('Observations')
    
    # Interpretación general
    interpretation = fields.Text('Clinical Interpretation')
    
    @classmethod
    def __setup__(cls):
        super(GnuHealthLabImmunoassay, cls).__setup__()
        cls._order = [('create_date', 'DESC')]
        cls._buttons.update({
            'start_process': {
                'invisible': Eval('state') != 'draft',
                'depends': ['state'],
            },
            'complete_process': {
                'invisible': Eval('state') != 'in_progress',
                'depends': ['state'],
            },
            'cancel': {
                'invisible': Eval('state').in_(['completed', 'cancelled']),
                'depends': ['state'],
            },
        })
    
    @staticmethod
    def default_state():
        return 'draft'
    
    def get_sample_info(self, name):
        """Obtiene información de la muestra del workflow"""
        if self.workflow_sample:
            if name == 'name':
                return self.workflow_sample.name
            elif name == 'patient':
                return self.workflow_sample.patient.id if self.workflow_sample.patient else None
            elif name == 'sample_type':
                # Retornar la descripción del tipo de muestra
                if self.workflow_sample.sample_type:
                    # Obtener la selección del modelo de workflow
                    selection = self.workflow_sample.fields_get(['sample_type'])['sample_type']['selection']
                    for code, desc in selection:
                        if code == self.workflow_sample.sample_type:
                            return desc
                return ''
        return None
    
    @classmethod
    @ModelView.button
    def start_process(cls, tests):
        cls.write(tests, {
            'state': 'in_progress',
            'processing_date': datetime.now(),
        })
        # Actualizar el estado de la muestra a 'processing' si no lo está
        for test in tests:
            if test.workflow_sample.state == 'received':
                Pool().get('gnuhealth.lab.workflow.sample').write(
                    [test.workflow_sample], {'state': 'processing'})
    
    @classmethod
    @ModelView.button
    def complete_process(cls, tests):
        cls.write(tests, {
            'state': 'completed',
            'delivery_date': datetime.now(),
        })
    
    @classmethod
    @ModelView.button
    def cancel(cls, tests):
        cls.write(tests, {
            'state': 'cancelled',
        })
    
    @classmethod
    def create(cls, vlist):
        """Override create para validaciones"""
        for values in vlist:
            # Verificar que no exista otro proceso activo para la misma muestra
            if 'workflow_sample' in values:
                existing = cls.search([
                    ('workflow_sample', '=', values['workflow_sample']),
                    ('state', 'in', ['draft', 'in_progress']),
                ])
                if existing:
                    raise UserWarning('immunoassay_exists',
                        'An active immunoassay process already exists for this sample.')
        
        return super(GnuHealthLabImmunoassay, cls).create(vlist)


class GnuHealthLabImmunoassayAntibody(ModelSQL, ModelView):
    'Immunoassay Antibody/Antigen'
    __name__ = 'gnuhealth.lab.immunoassay.antibody'
    
    immunoassay = fields.Many2One('gnuhealth.lab.immunoassay', 
        'Immunoassay', required=True, ondelete='CASCADE')
    
    test_type = fields.Selection([
        ('antibody', 'Antibody Detection'),
        ('antigen', 'Antigen Detection'),
        ('antibody_titer', 'Antibody Titer'),
    ], 'Test Type', required=True)
    
    name = fields.Char('Antibody/Antigen Name', required=True,
        help='Name of the antibody or antigen tested')
    
    method_specifics = fields.Char('Method Specifics',
        help='Specific method details (e.g., IgG, IgM, Total)')
    
    # Resultado cuantitativo
    quantitative_result = fields.Float('Quantitative Result',
        help='Numeric result value')
    
    unit = fields.Char('Unit',
        help='Unit of measurement (e.g., IU/mL, ng/mL, index)')
    
    # Resultado cualitativo
    qualitative_result = fields.Selection([
        (None, ''),
        ('positive', 'Positive'),
        ('negative', 'Negative'),
        ('equivocal', 'Equivocal'),
        ('borderline', 'Borderline'),
    ], 'Qualitative Result')
    
    # Valores de referencia
    reference_range = fields.Char('Reference Range',
        help='Normal reference range')
    
    cutoff_value = fields.Float('Cutoff Value',
        help='Cutoff value for positive/negative determination')
    
    # Interpretación
    interpretation = fields.Selection([
        (None, ''),
        ('reactive', 'Reactive'),
        ('non_reactive', 'Non-Reactive'),
        ('indeterminate', 'Indeterminate'),
        ('low_titer', 'Low Titer'),
        ('high_titer', 'High Titer'),
    ], 'Interpretation')
    
    observations = fields.Text('Observations')
    
    @staticmethod
    def default_test_type():
        return 'antibody'