#!/usr/bin/env python
# -*- coding: utf-8 -*-

from trytond.model import ModelView, ModelSQL, fields
from trytond.pool import Pool
from trytond.pyson import Eval, Bool
from trytond.exceptions import UserWarning
from datetime import datetime

__all__ = ['GnuHealthLabHistopathology', 'GnuHealthLabHistopathologyAntibody']


class GnuHealthLabHistopathology(ModelSQL, ModelView):
    'Lab Histopathology Process'
    __name__ = 'gnuhealth.lab.histopathology'
    
    # Relación con la muestra del workflow
    workflow_sample = fields.Many2One('gnuhealth.lab.workflow.sample', 
        'Workflow Sample', required=True, ondelete='CASCADE',
        domain=[('state', 'in', ['received', 'processing'])],
        help='Sample being processed in histopathology')
    
    # Información básica (campos función desde workflow_sample)
    name = fields.Function(fields.Char('Order Number'), 'get_sample_info')
    patient = fields.Function(fields.Many2One('gnuhealth.patient', 'Patient'), 
        'get_sample_info')
    sample_type = fields.Function(fields.Char('Sample Type'), 'get_sample_info')
    
    # Tipo de estudio histopatológico
    study_type = fields.Selection([
        ('routine', 'Routine Histopathology'),
        ('histochemistry', 'Histochemistry'),
        ('immunohistochemistry', 'Immunohistochemistry'),
        ('fish', 'FISH (Fluorescence In Situ Hybridization)'),
        ('cytology', 'Cytology'),
    ], 'Study Type', required=True,
    help='Type of histopathology study')
    
    # SECCIÓN 1: Macroscopía
    macroscopy_date = fields.DateTime('Macroscopy Date',
        states={'invisible': Eval('study_type').in_(['cytology'])},
        depends=['study_type'])
    
    number_of_cuts = fields.Integer('Number of Cuts',
        states={'invisible': Eval('study_type').in_(['cytology'])},
        depends=['study_type'])
    
    number_of_cassettes = fields.Integer('Number of Cassettes',
        states={'invisible': Eval('study_type').in_(['cytology'])},
        depends=['study_type'])
    
    macroscopy_observations = fields.Text('Macroscopy Observations')
    
    # SECCIÓN 2: Procesamiento
    processing_date = fields.DateTime('Processing Date',
        states={'invisible': Eval('study_type').in_(['cytology'])},
        depends=['study_type'])
    
    inclusion_date = fields.DateTime('Inclusion Date',
        states={'invisible': Eval('study_type').in_(['cytology'])},
        depends=['study_type'],
        help='Date of paraffin inclusion')
    
    # SECCIÓN 3: Corte y Tinción
    cutting_date = fields.DateTime('Cutting Date')
    
    staining_date = fields.DateTime('Staining Date')
    
    # SECCIÓN 4: Anticuerpos/Marcadores (para histoquímica, IHQ y FISH)
    antibodies = fields.One2Many('gnuhealth.lab.histopathology.antibody', 
        'histopathology', 'Antibodies/Markers',
        states={'invisible': ~Eval('study_type').in_(['histochemistry', 
                                                      'immunohistochemistry', 
                                                      'fish'])},
        depends=['study_type'])
    
    # SECCIÓN 5: Finalización
    delivery_date = fields.DateTime('Delivery Date')
    
    responsible_professional = fields.Many2One('gnuhealth.healthprofessional',
        'Responsible Professional', required=True,
        help='Professional responsible for the complete process')
    
    # Estado del proceso
    state = fields.Selection([
        ('draft', 'Draft'),
        ('macroscopy', 'Macroscopy'),
        ('processing', 'Processing'),
        ('cutting', 'Cutting'),
        ('staining', 'Staining'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ], 'State', readonly=True, required=True)
    
    # Observaciones generales
    observations = fields.Text('General Observations')
    
    # Resultado/Diagnóstico
    diagnosis = fields.Text('Diagnosis')
    
    @classmethod
    def __setup__(cls):
        super(GnuHealthLabHistopathology, cls).__setup__()
        cls._order = [('create_date', 'DESC')]
        cls._buttons.update({
            'start_macroscopy': {
                'invisible': (Eval('state') != 'draft') | 
                           Eval('study_type').in_(['cytology']),
                'depends': ['state', 'study_type'],
            },
            'complete_macroscopy': {
                'invisible': (Eval('state') != 'macroscopy') |
                           Eval('study_type').in_(['cytology']),
                'depends': ['state', 'study_type'],
            },
            'complete_processing': {
                'invisible': (Eval('state') != 'processing') |
                           Eval('study_type').in_(['cytology']),
                'depends': ['state', 'study_type'],
            },
            'complete_cutting': {
                'invisible': ~Eval('state').in_(['cutting', 'draft']),
                'depends': ['state'],
            },
            'complete_staining': {
                'invisible': Eval('state') != 'staining',
                'depends': ['state'],
            },
            'complete_process': {
                'invisible': ~Eval('state').in_(['staining', 'cutting']),
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
    def start_macroscopy(cls, tests):
        cls.write(tests, {
            'state': 'macroscopy',
            'macroscopy_date': datetime.now(),
        })
        # Actualizar el estado de la muestra a 'processing' si no lo está
        for test in tests:
            if test.workflow_sample.state == 'received':
                Pool().get('gnuhealth.lab.workflow.sample').write(
                    [test.workflow_sample], {'state': 'processing'})
    
    @classmethod
    @ModelView.button
    def complete_macroscopy(cls, tests):
        # Validar que los campos requeridos estén llenos antes de completar
        for test in tests:
            if test.study_type != 'cytology':
                if not test.number_of_cuts:
                    raise UserWarning('missing_cuts',
                        'Number of cuts is required to complete macroscopy.')
                if not test.number_of_cassettes:
                    raise UserWarning('missing_cassettes',
                        'Number of cassettes is required to complete macroscopy.')
        
        cls.write(tests, {
            'state': 'processing',
            'processing_date': datetime.now(),
        })
    
    @classmethod
    @ModelView.button
    def complete_processing(cls, tests):
        cls.write(tests, {
            'state': 'cutting',
        })
    
    @classmethod
    @ModelView.button
    def complete_cutting(cls, tests):
        cls.write(tests, {
            'state': 'staining',
            'cutting_date': datetime.now() if not tests[0].cutting_date else tests[0].cutting_date,
        })
    
    @classmethod
    @ModelView.button
    def complete_staining(cls, tests):
        cls.write(tests, {
            'state': 'completed',
            'staining_date': datetime.now() if not tests[0].staining_date else tests[0].staining_date,
            'delivery_date': datetime.now(),
        })
    
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
        """Override create para validaciones y flujo especial de citología"""
        for values in vlist:
            # Verificar que no exista otro proceso activo para la misma muestra
            if 'workflow_sample' in values:
                existing = cls.search([
                    ('workflow_sample', '=', values['workflow_sample']),
                    ('state', 'in', ['draft', 'macroscopy', 'processing', 
                                     'cutting', 'staining']),
                ])
                if existing:
                    raise UserWarning('histopathology_exists',
                        'An active histopathology process already exists for this sample.')
            
            # Si es citología, saltar directamente a 'cutting'
            if values.get('study_type') == 'cytology':
                values['state'] = 'cutting'
        
        return super(GnuHealthLabHistopathology, cls).create(vlist)


class GnuHealthLabHistopathologyAntibody(ModelSQL, ModelView):
    'Histopathology Antibody/Marker'
    __name__ = 'gnuhealth.lab.histopathology.antibody'
    
    histopathology = fields.Many2One('gnuhealth.lab.histopathology', 
        'Histopathology', required=True, ondelete='CASCADE')
    
    antibody_type = fields.Selection([
        ('primary', 'Primary Antibody'),
        ('secondary', 'Secondary Antibody'),
        ('marker', 'Marker'),
        ('probe', 'Probe'),
        ('stain', 'Special Stain'),
    ], 'Type', required=True)
    
    name = fields.Char('Name/Code', required=True,
        help='Antibody or marker name/code')
    
    clone = fields.Char('Clone',
        help='Antibody clone if applicable')
    
    dilution = fields.Char('Dilution',
        help='Dilution used (e.g., 1:100)')
    
    result = fields.Selection([
        (None, ''),
        ('positive', 'Positive'),
        ('negative', 'Negative'),
        ('focal_positive', 'Focal Positive'),
        ('weak_positive', 'Weak Positive'),
        ('strong_positive', 'Strong Positive'),
        ('equivocal', 'Equivocal'),
    ], 'Result')
    
    percentage = fields.Integer('Percentage (%)',
        help='Percentage of positive cells if applicable')
    
    intensity = fields.Selection([
        (None, ''),
        ('1+', '1+'),
        ('2+', '2+'),
        ('3+', '3+'),
    ], 'Intensity')
    
    observations = fields.Text('Observations')
    
    @staticmethod
    def default_antibody_type():
        return 'primary'