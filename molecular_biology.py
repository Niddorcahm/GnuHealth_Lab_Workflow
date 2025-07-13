#!/usr/bin/env python
# -*- coding: utf-8 -*-

from trytond.model import ModelView, ModelSQL, fields
from trytond.pool import Pool
from trytond.pyson import Eval, Bool
from trytond.exceptions import UserWarning
from datetime import datetime

__all__ = ['GnuHealthLabMolecularBiology']


class GnuHealthLabMolecularBiology(ModelSQL, ModelView):
    'Lab Molecular Biology Process'
    __name__ = 'gnuhealth.lab.molecular_biology'
    
    # Relación con la muestra del workflow
    workflow_sample = fields.Many2One('gnuhealth.lab.workflow.sample', 
        'Workflow Sample', required=True, ondelete='CASCADE',
        domain=[('state', 'in', ['received', 'processing'])],
        help='Sample being processed in molecular biology')
    
    # Información básica (campos función desde workflow_sample)
    name = fields.Function(fields.Char('Order Number'), 'get_sample_info')
    patient = fields.Function(fields.Many2One('gnuhealth.patient', 'Patient'), 
        'get_sample_info')
    sample_type = fields.Function(fields.Char('Sample Type'), 'get_sample_info')
    
    # Tipo de estudio molecular
    study_type = fields.Selection([
        ('pcr_endpoint', 'PCR Endpoint'),
        ('qpcr', 'qPCR (Real-time PCR)'),
        ('rt_pcr', 'RT-PCR'),
        ('sequencing', 'Sequencing'),
        ('extraction_only', 'Genetic Material Extraction Only'),
        ('electrophoresis', 'Protein Electrophoresis'),
    ], 'Study Type', required=True,
    help='Type of molecular biology study')
    
    # SECCIÓN 1: Extracción de Material Genético
    extraction_date = fields.DateTime('Extraction Date')
    
    genetic_material_type = fields.Selection([
        (None, ''),  # Opción vacía
        ('dna', 'DNA'),
        ('rna', 'RNA'),
        ('total_rna', 'Total RNA'),
        ('mrna', 'mRNA'),
        ('mirna', 'miRNA'),
        ('protein', 'Protein'),
    ], 'Genetic Material Type')
    
    # Concentración y pureza
    concentration = fields.Float('Concentration (ng/µL)',
        help='Concentration of extracted genetic material')
    
    purity_260_280 = fields.Float('Purity (260/280)',
        help='Ratio of absorbance at 260nm and 280nm')
    
    purity_260_230 = fields.Float('Purity (260/230)',
        help='Ratio of absorbance at 260nm and 230nm')
    
    extraction_kit = fields.Char('Extraction Kit',
        help='Name and brand of extraction kit used')
    
    extraction_professional = fields.Many2One('gnuhealth.healthprofessional',
        'Extraction Professional', 
        help='Professional who performed the extraction')
    
    extraction_completed = fields.Boolean('Extraction Completed')
    
    # SECCIÓN 2: PCR
    pcr_pre_date = fields.DateTime('Pre-transcriptional PCR Date',
        states={'invisible': ~Eval('study_type').in_(['rt_pcr'])},
        depends=['study_type'])
    
    pcr_post_date = fields.DateTime('Post-transcriptional PCR Date',
        states={'invisible': ~Eval('study_type').in_(['rt_pcr'])},
        depends=['study_type'])
    
    pcr_date = fields.DateTime('PCR Date',
        states={'invisible': Eval('study_type').in_(['rt_pcr'])},
        depends=['study_type'])
    
    pcr_kit = fields.Char('PCR Kit',
        help='Name and brand of PCR kit used',
        states={'invisible': Eval('study_type').in_(['extraction_only'])},
        depends=['study_type'])
    
    pcr_completed = fields.Boolean('PCR Completed')
    
    # Resultados PCR
    pcr_result = fields.Selection([
        (None, ''),  # Opción vacía
        ('positive', 'Positive'),
        ('negative', 'Negative'),
        ('indeterminate', 'Indeterminate'),
    ], 'PCR Result',
    states={'invisible': Eval('study_type').in_(['extraction_only', 'electrophoresis'])},
    depends=['study_type'])
    
    ct_value = fields.Float('Ct Value',
        help='Cycle threshold value for qPCR',
        states={'invisible': ~Eval('study_type').in_(['qpcr'])},
        depends=['study_type'])
    
    # SECCIÓN 3: Electroforesis
    gel_date = fields.DateTime('Gel Preparation Date',
        states={'invisible': ~Eval('study_type').in_(['pcr_endpoint', 'rt_pcr', 
                                                      'electrophoresis'])},
        depends=['study_type'])
    
    gel_type = fields.Selection([
        (None, ''),  # Opción vacía
        ('agarose_1', 'Agarose 1%'),
        ('agarose_15', 'Agarose 1.5%'),
        ('agarose_2', 'Agarose 2%'),
        ('polyacrylamide', 'Polyacrylamide'),
        ('sds_page', 'SDS-PAGE'),
        ('other', 'Other'),
    ], 'Gel Type',
    states={'invisible': ~Eval('study_type').in_(['pcr_endpoint', 'rt_pcr', 
                                                  'electrophoresis'])},
    depends=['study_type'])
    
    gel_completed = fields.Boolean('Gel Electrophoresis Completed')
    
    # SECCIÓN 4: Finalización
    delivery_date = fields.DateTime('Delivery Date')
    
    responsible_professional = fields.Many2One('gnuhealth.healthprofessional',
        'Responsible Professional', required=True,
        help='Professional responsible for the complete process')
    
    # Estado del proceso
    state = fields.Selection([
        ('draft', 'Draft'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ], 'State', readonly=True, required=True)
    
    # Observaciones
    observations = fields.Text('Observations')
    
    @classmethod
    def __setup__(cls):
        super(GnuHealthLabMolecularBiology, cls).__setup__()
        cls._order = [('create_date', 'DESC')]
        cls._buttons.update({
            'start_process': {
                'invisible': Eval('state') != 'draft',
                'depends': ['state'],
            },
            'complete_extraction': {
                'invisible': (~Eval('state').in_(['in_progress']) | 
                            Bool(Eval('extraction_completed'))),
                'depends': ['state', 'extraction_completed'],
            },
            'complete_pcr': {
                'invisible': (~Eval('state').in_(['in_progress']) | 
                            Bool(Eval('pcr_completed')) |
                            ~Bool(Eval('extraction_completed')) |
                            Eval('study_type').in_(['extraction_only'])),
                'depends': ['state', 'pcr_completed', 'extraction_completed', 'study_type'],
            },
            'complete_gel': {
                'invisible': (~Eval('state').in_(['in_progress']) | 
                            Bool(Eval('gel_completed')) |
                            ~Bool(Eval('pcr_completed')) |
                            ~Eval('study_type').in_(['pcr_endpoint', 'rt_pcr', 
                                                    'electrophoresis'])),
                'depends': ['state', 'gel_completed', 'pcr_completed', 'study_type'],
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
    
    @staticmethod
    def default_extraction_completed():
        return False
    
    @staticmethod
    def default_pcr_completed():
        return False
    
    @staticmethod
    def default_gel_completed():
        return False
    
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
        })
        # Actualizar el estado de la muestra a 'processing' si no lo está
        for test in tests:
            if test.workflow_sample.state == 'received':
                Pool().get('gnuhealth.lab.workflow.sample').write(
                    [test.workflow_sample], {'state': 'processing'})
    
    @classmethod
    @ModelView.button
    def complete_extraction(cls, tests):
        # Validar campos requeridos antes de completar
        for test in tests:
            if not test.extraction_date:
                raise UserWarning('missing_extraction_date',
                    'Extraction date is required to complete this step.')
            if not test.genetic_material_type:
                raise UserWarning('missing_material_type',
                    'Genetic material type is required to complete extraction.')
            if not test.extraction_kit:
                raise UserWarning('missing_extraction_kit',
                    'Extraction kit information is required.')
            if not test.extraction_professional:
                raise UserWarning('missing_professional',
                    'Extraction professional is required.')
        
        cls.write(tests, {
            'extraction_completed': True,
        })
    
    @classmethod
    @ModelView.button
    def complete_pcr(cls, tests):
        # Validar campos requeridos según el tipo de estudio
        for test in tests:
            if test.study_type == 'rt_pcr':
                if not test.pcr_pre_date or not test.pcr_post_date:
                    raise UserWarning('missing_pcr_dates',
                        'Both pre and post-transcriptional PCR dates are required for RT-PCR.')
            elif test.study_type not in ['extraction_only']:
                if not test.pcr_date:
                    raise UserWarning('missing_pcr_date',
                        'PCR date is required to complete this step.')
            
            if test.study_type not in ['extraction_only'] and not test.pcr_kit:
                raise UserWarning('missing_pcr_kit',
                    'PCR kit information is required.')
        
        cls.write(tests, {
            'pcr_completed': True,
        })
    
    @classmethod
    @ModelView.button
    def complete_gel(cls, tests):
        # Validar campos requeridos para electroforesis
        for test in tests:
            if test.study_type in ['pcr_endpoint', 'rt_pcr', 'electrophoresis']:
                if not test.gel_date:
                    raise UserWarning('missing_gel_date',
                        'Gel preparation date is required to complete this step.')
                if not test.gel_type:
                    raise UserWarning('missing_gel_type',
                        'Gel type is required to complete electrophoresis.')
        
        cls.write(tests, {
            'gel_completed': True,
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
        """Override create para validaciones"""
        for values in vlist:
            # Verificar que no exista otro proceso molecular activo para la misma muestra
            if 'workflow_sample' in values:
                existing = cls.search([
                    ('workflow_sample', '=', values['workflow_sample']),
                    ('state', 'in', ['draft', 'in_progress']),
                ])
                if existing:
                    raise UserWarning('molecular_exists',
                        'An active molecular biology process already exists for this sample.')
        
        return super(GnuHealthLabMolecularBiology, cls).create(vlist)