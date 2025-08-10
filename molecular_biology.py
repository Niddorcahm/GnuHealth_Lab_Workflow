#!/usr/bin/env python
# -*- coding: utf-8 -*-

from trytond.model import ModelView, ModelSQL, fields
from trytond.pool import Pool
from trytond.pyson import Eval, Bool
from trytond.exceptions import UserWarning
from datetime import datetime

__all__ = ['GnuHealthLabMolecularBiology', 'GnuHealthLabMolecularBiologyAntibody']


class GnuHealthLabMolecularBiology(ModelSQL, ModelView):
    'Lab Molecular Biology Process'
    __name__ = 'gnuhealth.lab.molecular_biology'

    # Relación con la muestra del workflow
    workflow_sample = fields.Many2One('gnuhealth.lab.workflow.sample',
                                      'Workflow Sample', required=True, ondelete='CASCADE',
                                      domain=[('state', 'in', ['received', 'processing'])],
                                      help='Sample being processed in molecular biology')

    # Información básica (campos función desde workflow_sample)
    name = fields.Function(fields.Char('Order Number'), 'get_sample_info', searcher='search_sample_info')
    patient = fields.Function(fields.Many2One('gnuhealth.patient', 'Patient'),
                              'get_sample_info')
    sample_type = fields.Function(fields.Char('Sample Type'), 'get_sample_info')

    # Tipo de análisis molecular
    analysis_type = fields.Selection([
        ('pcr', 'PCR'),
        ('qpcr', 'qPCR/Real-time PCR'),
        ('sequencing', 'DNA Sequencing'),
        ('electrophoresis', 'Electrophoresis'),
        ('blotting', 'Blotting (Southern/Northern/Western)'),
        ('microarray', 'Microarray'),
        ('fish', 'FISH'),
        ('other', 'Other'),
    ], 'Analysis Type', required=True,
        help='Type of molecular biology analysis')

    # Profesional responsable
    responsible_professional = fields.Many2One('gnuhealth.healthprofessional',
                                               'Responsible Professional', required=True,
                                               help='Professional responsible for the analysis')

    # Fechas del proceso
    processing_date = fields.DateTime('Processing Date')
    delivery_date = fields.DateTime('Delivery Date')

    # Estado del proceso
    state = fields.Selection([
        ('draft', 'Draft'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ], 'State', readonly=True, required=True)

    # Observaciones generales
    observations = fields.Text('General Observations')

    # Resultado/Análisis
    analysis_result = fields.Text('Analysis Result')

    # Anticuerpos/Marcadores para análisis molecular
    antibodies = fields.One2Many('gnuhealth.lab.molecular_biology.antibody',
                                 'molecular_biology', 'Antibodies/Markers',
                                 help='Antibodies or molecular markers used in the analysis')

    @classmethod
    def __setup__(cls):
        super(GnuHealthLabMolecularBiology, cls).__setup__()
        cls._order = [('create_date', 'DESC')]
        cls._buttons.update({
            'start_process': {
                'invisible': Eval('state') != 'draft',
                'depends': ['state'],
            },
            'complete_process': {
                'invisible': Eval('state') != 'processing',
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
                if self.workflow_sample.sample_type:
                    selection = self.workflow_sample.fields_get(['sample_type'])['sample_type']['selection']
                    for code, desc in selection:
                        if code == self.workflow_sample.sample_type:
                            return desc
                return ''
        return None

    @classmethod
    def search_sample_info(cls, name, clause):
        """Searcher method for the name field (Order Number)"""
        field, operator, value = clause

        if name == 'name':
            pool = Pool()
            WorkflowSample = pool.get('gnuhealth.lab.workflow.sample')

            workflow_samples = WorkflowSample.search([
                ('name', operator, value)
            ])

            if workflow_samples:
                workflow_sample_ids = [ws.id for ws in workflow_samples]
                return [('workflow_sample', 'in', workflow_sample_ids)]
            else:
                return [('id', '=', 0)]
        else:
            return [('workflow_sample.name', operator, value)]

    @classmethod
    @ModelView.button
    def start_process(cls, tests):
        cls.write(tests, {
            'state': 'processing',
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
                    ('state', 'in', ['draft', 'processing']),
                ])
                if existing:
                    raise UserWarning('molecular_biology_exists',
                                      'An active molecular biology process already exists for this sample.')

        return super(GnuHealthLabMolecularBiology, cls).create(vlist)


class GnuHealthLabMolecularBiologyAntibody(ModelSQL, ModelView):
    'Molecular Biology Antibody/Marker'
    __name__ = 'gnuhealth.lab.molecular_biology.antibody'

    molecular_biology = fields.Many2One('gnuhealth.lab.molecular_biology',
                                        'Molecular Biology', required=True, ondelete='CASCADE')

    antibody_type = fields.Selection([
        ('primary', 'Primary Antibody'),
        ('secondary', 'Secondary Antibody'),
        ('marker', 'Molecular Marker'),
        ('probe', 'Probe'),
        ('primer', 'Primer'),
    ], 'Antibody/Marker Type', help="Type of antibody or molecular marker")

    name = fields.Char('Name/Code', required=True,
                       help='Antibody or marker name/code')

    sequence = fields.Text('Sequence',
                           help='DNA/RNA sequence if applicable')

    concentration = fields.Char('Concentration',
                                help='Working concentration')

    dilution = fields.Char('Dilution',
                           help='Dilution used (e.g., 1:100)')

    incubation_time = fields.Char('Incubation Time',
                                  help='Time of incubation')

    temperature = fields.Char('Temperature',
                              help='Incubation temperature')

    result = fields.Selection([
        (None, ''),
        ('positive', 'Positive'),
        ('negative', 'Negative'),
        ('weak', 'Weak'),
        ('strong', 'Strong'),
        ('amplified', 'Amplified'),
        ('not_amplified', 'Not Amplified'),
    ], 'Result')

    intensity = fields.Selection([
        (None, ''),
        ('1+', '1+'),
        ('2+', '2+'),
        ('3+', '3+'),
    ], 'Intensity')

    pattern = fields.Char('Pattern',
                          help='Pattern description')

    observations = fields.Text('Observations')

    @staticmethod
    def default_antibody_type():
        return 'primer'
