#!/usr/bin/env python
# -*- coding: utf-8 -*-

from trytond.model import ModelView, ModelSQL, fields
from trytond.pool import Pool, PoolMeta
from trytond.pyson import Eval
from trytond.wizard import Wizard, StateView, StateTransition, Button
from trytond.transaction import Transaction
from trytond.exceptions import UserWarning
from datetime import datetime

__all__ = ['GnuHealthLabWorkflowSample', 'GnuHealthLab', 
           'CreateLabWorkflowStart', 'CreateLabWorkflowWizard']

# Definición de tipos de muestra
SAMPLE_TYPES = [
    ('blood', 'Blood'),
    ('urine', 'Urine'),
    ('stool', 'Stool'),
    ('tissue_formalin', 'Tissue Fixed in Formalin'),
    ('tissue_paraffin', 'Paraffin Block'),
    ('smear_exfoliative', 'Exfoliative Smear'),
    ('smear_puncture', 'Puncture Smear'),
    ('secretion', 'Secretion'),
    ('sputum', 'Sputum'),
    ('saliva', 'Saliva'),
    ('csf', 'Cerebrospinal Fluid'),
    ('other', 'Other'),
]


def get_institution():
    """Función auxiliar para obtener la institución"""
    try:
        from .core_imports import get_institution as gi
        return gi()
    except ImportError:
        return None


class GnuHealthLabWorkflowSample(ModelSQL, ModelView):
    'Lab Workflow Sample'
    __name__ = 'gnuhealth.lab.workflow.sample'
    
    # El número de orden que sigue a la muestra en todo el proceso
    name = fields.Char('Order Number', readonly=True, required=True,
        help='Original order number that follows the sample through all processes')
    
    # Relación directa con la orden de laboratorio
    lab_test = fields.Many2One('gnuhealth.lab', 'Lab Test Order', 
        required=True, ondelete='CASCADE',
        help='Lab test order this sample belongs to')
    
    # ID del test de laboratorio (campo función)
    lab_test_id = fields.Function(fields.Char('Lab Test ID'),
        'get_lab_test_id')
    
    # Información del paciente (campo función desde lab_test)
    patient = fields.Function(fields.Many2One('gnuhealth.patient', 'Patient'),
        'get_patient')
    
    # Establecimiento de origen
    origin_institution = fields.Many2One('gnuhealth.institution',
        'Origin Institution',
        help='Healthcare institution where the sample was collected')
    
    # Tipo de muestra
    sample_type = fields.Selection(SAMPLE_TYPES, 'Sample Type', required=True)
    
    # Estado del workflow
    state = fields.Selection([
        ('pending', 'Pending Collection'),
        ('collected', 'Collected'),
        ('in_transit', 'In Transit'),
        ('received', 'Received at Lab'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('rejected', 'Rejected'),
    ], 'State', readonly=True, required=True)
    
    # Fechas del proceso
    collection_date = fields.DateTime('Collection Date',
        states={'required': ~Eval('state').in_(['pending'])})
    received_date = fields.DateTime('Received Date',
        states={'invisible': Eval('state').in_(['pending', 'collected'])})
    completion_date = fields.DateTime('Completion Date',
        states={'invisible': ~Eval('state').in_(['completed'])})
    
    # Notas
    notes = fields.Text('Notes')
    
    # Campo función para verificar si todos los procesos están completos
    all_processes_completed = fields.Function(fields.Boolean('All Processes Completed'),
        'get_all_processes_completed')
    
    @classmethod
    def __setup__(cls):
        super(GnuHealthLabWorkflowSample, cls).__setup__()
        cls._order = [('create_date', 'DESC')]
        cls._buttons.update({
            'collect': {
                'invisible': Eval('state') != 'pending',
            },
            'receive': {
                'invisible': ~Eval('state').in_(['collected', 'in_transit']),
            },
            'process': {
                'invisible': Eval('state') != 'received',
            },
            'complete': {
                'invisible': Eval('state') != 'processing',
            },
            'reject': {
                'invisible': Eval('state').in_(['completed', 'rejected']),
            },
            'create_molecular_biology': {
                'invisible': ~Eval('state').in_(['received', 'processing']),
            },
            'create_histopathology': {
                'invisible': ~Eval('state').in_(['received', 'processing']),
            },
            'create_immunoassay': {
                'invisible': ~Eval('state').in_(['received', 'processing']),
            },
            'auto_complete': {
                'invisible': (~Eval('all_processes_completed') | 
                           (Eval('state') != 'processing')),
                'depends': ['all_processes_completed', 'state'],
            },
        })
    
    @staticmethod
    def default_state():
        return 'pending'
    
    @staticmethod
    def default_sample_type():
        return 'blood'
    
    @staticmethod
    def default_origin_institution():
        return get_institution()
    
    def get_patient(self, name):
        """Obtiene el paciente desde la orden de laboratorio"""
        if self.lab_test and self.lab_test.patient:
            return self.lab_test.patient.id
        return None
    
    def get_lab_test_id(self, name):
        """Obtiene el ID del test de laboratorio"""
        if self.lab_test:
            return self.lab_test.name
        return ''
    
    def get_all_processes_completed(self, name):
        """Verifica si todos los procesos están completados"""
        pool = Pool()
        
        # Verificar procesos de biología molecular
        MolecularBiology = pool.get('gnuhealth.lab.molecular_biology')
        molecular_processes = MolecularBiology.search([
            ('workflow_sample', '=', self.id),
            ('state', 'not in', ['completed', 'cancelled']),
        ])
        
        # Verificar procesos de histopatología
        try:
            Histopathology = pool.get('gnuhealth.lab.histopathology')
            histopathology_processes = Histopathology.search([
                ('workflow_sample', '=', self.id),
                ('state', 'not in', ['completed', 'cancelled']),
            ])
        except:
            histopathology_processes = []
        
        # Verificar procesos de inmunoensayo
        try:
            Immunoassay = pool.get('gnuhealth.lab.immunoassay')
            immunoassay_processes = Immunoassay.search([
                ('workflow_sample', '=', self.id),
                ('state', 'not in', ['completed', 'cancelled']),
            ])
        except:
            immunoassay_processes = []
        
        # Si hay procesos activos, no está completo
        if molecular_processes or histopathology_processes or immunoassay_processes:
            return False
        
        # Verificar que al menos haya un proceso completado
        # (no queremos auto-completar si no hay procesos)
        total_molecular = len(MolecularBiology.search([
            ('workflow_sample', '=', self.id),
        ]))
        
        try:
            Histopathology = pool.get('gnuhealth.lab.histopathology')
            total_histopathology = len(Histopathology.search([
                ('workflow_sample', '=', self.id),
            ]))
        except:
            total_histopathology = 0
        
        try:
            Immunoassay = pool.get('gnuhealth.lab.immunoassay')
            total_immunoassay = len(Immunoassay.search([
                ('workflow_sample', '=', self.id),
            ]))
        except:
            total_immunoassay = 0
        
        # Si hay al menos un proceso y ninguno está activo, está completo
        total_processes = total_molecular + total_histopathology + total_immunoassay
        return total_processes > 0
    
    @fields.depends('lab_test')
    def on_change_lab_test(self):
        """Actualiza el name cuando se asigna un lab_test"""
        if self.lab_test and hasattr(self.lab_test, 'request_order') and self.lab_test.request_order:
            self.name = str(self.lab_test.request_order)
    
    @classmethod
    def create(cls, vlist):
        """Override create para asegurar que name se establezca correctamente"""
        vlist = [x.copy() for x in vlist]
        for values in vlist:
            if 'lab_test' in values and not values.get('name'):
                # Obtener el lab test para copiar su request_order
                Lab = Pool().get('gnuhealth.lab')
                lab = Lab(values['lab_test'])
                if hasattr(lab, 'request_order') and lab.request_order is not None:
                    values['name'] = str(lab.request_order)
        return super(GnuHealthLabWorkflowSample, cls).create(vlist)
    
    @classmethod
    @ModelView.button
    def collect(cls, samples):
        cls.write(samples, {
            'state': 'collected',
            'collection_date': datetime.now(),
        })
    
    @classmethod
    @ModelView.button
    def receive(cls, samples):
        cls.write(samples, {
            'state': 'received',
            'received_date': datetime.now(),
        })
    
    @classmethod
    @ModelView.button
    def process(cls, samples):
        cls.write(samples, {
            'state': 'processing',
        })
    
    @classmethod
    @ModelView.button
    def complete(cls, samples):
        cls.write(samples, {
            'state': 'completed',
            'completion_date': datetime.now(),
        })
    
    @classmethod
    @ModelView.button
    def auto_complete(cls, samples):
        """Completa automáticamente cuando todos los procesos están terminados"""
        cls.write(samples, {
            'state': 'completed',
            'completion_date': datetime.now(),
        })
    
    @classmethod
    @ModelView.button
    def reject(cls, samples):
        cls.write(samples, {
            'state': 'rejected',
        })
    
    @classmethod
    @ModelView.button_action('health_lab_workflow.wizard_create_molecular_biology')
    def create_molecular_biology(cls, samples):
        pass
    
    @classmethod
    @ModelView.button_action('health_lab_workflow.wizard_create_histopathology')
    def create_histopathology(cls, samples):
        pass
    
    @classmethod
    @ModelView.button_action('health_lab_workflow.wizard_create_immunoassay')
    def create_immunoassay(cls, samples):
        pass
    
    @classmethod
    @ModelView.button_action('health_lab.wizard_create_lab_test')
    def create_lab_test(cls, samples):
        """Acción para crear Lab Test usando el wizard del módulo health_lab"""
        pass


class GnuHealthLab(metaclass=PoolMeta):
    __name__ = 'gnuhealth.lab'
    
    # Agregar la relación con las muestras del workflow
    workflow_samples = fields.One2Many('gnuhealth.lab.workflow.sample', 
        'lab_test', 'Workflow Samples',
        help='Track sample collection and processing')
    
    # Campo para mostrar el estado actual de la muestra principal
    sample_state = fields.Function(fields.Selection([
        ('pending', 'Pending Collection'),
        ('collected', 'Collected'),
        ('in_transit', 'In Transit'),
        ('received', 'Received at Lab'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('rejected', 'Rejected'),
        ('no_sample', 'No Sample'),
    ], 'Sample State'), 'get_sample_state')
    
    def get_sample_state(self, name):
        """Obtiene el estado de la muestra principal"""
        if self.workflow_samples:
            # Retorna el estado de la primera muestra (o la más reciente)
            return self.workflow_samples[0].state
        return 'no_sample'


class CreateLabWorkflowStart(ModelView):
    'Create Lab Workflow Sample'
    __name__ = 'gnuhealth.create_lab_workflow.start'
    
    sample_type = fields.Selection(SAMPLE_TYPES, 'Sample Type', required=True)
    
    notes = fields.Text('Notes')
    
    # Campo de institución de origen
    origin_institution = fields.Many2One('gnuhealth.institution',
        'Origin Institution',
        help='Healthcare institution where the sample was collected')
    
    @staticmethod
    def default_sample_type():
        return 'blood'
    
    @staticmethod
    def default_origin_institution():
        return get_institution()


class CreateLabWorkflowWizard(Wizard):
    'Create Lab Workflow'
    __name__ = 'gnuhealth.create_lab_workflow'
    
    start = StateView('gnuhealth.create_lab_workflow.start',
        'health_lab_workflow.create_lab_workflow_start_form', [
            Button('Cancel', 'end', 'tryton-cancel'),
            Button('Create', 'create_workflow', 'tryton-ok', default=True),
        ])
    create_workflow = StateTransition()
    
    def transition_create_workflow(self):
        pool = Pool()
        LabTestRequest = pool.get('gnuhealth.patient.lab.test')
        Lab = pool.get('gnuhealth.lab')
        Sample = pool.get('gnuhealth.lab.workflow.sample')
        
        # Obtener el lab test request actual
        lab_test_request = LabTestRequest(Transaction().context['active_id'])
        
        # Verificar el estado
        if lab_test_request.state != 'draft':
            raise UserWarning('invalid_state',
                'Lab Test Request must be in draft state to create workflow.')
        
        # Crear o buscar el Lab Result
        lab_results = Lab.search([
            ('request_order', '=', lab_test_request.request),
        ])
        
        if lab_results:
            lab_result = lab_results[0]
        else:
            # Crear nuevo Lab Result
            lab_result = Lab()
            lab_result.request_order = lab_test_request.request
            # 'name' en lab_test_request es el tipo de test (Many2One)
            lab_result.test = lab_test_request.name
            # Copiar el tipo de fuente (patient o other_source)
            lab_result.source_type = lab_test_request.source_type
            if lab_test_request.source_type == 'patient':
                lab_result.patient = lab_test_request.patient_id
            else:
                lab_result.other_source = lab_test_request.other_source
            lab_result.requestor = lab_test_request.doctor_id
            lab_result.date_requested = lab_test_request.date
            lab_result.save()
        
        # Verificar si ya existe un workflow
        existing = Sample.search([
            ('lab_test', '=', lab_result.id),
        ])
        
        if existing:
            raise UserWarning('workflow_exists',
                'A workflow sample already exists for this lab test.')
        
        # Crear el registro de workflow
        sample = Sample()
        sample.lab_test = lab_result
        sample.name = str(lab_result.request_order)  # Usar el número de orden original
        sample.sample_type = self.start.sample_type
        sample.notes = self.start.notes
        # Copiar la institución de origen
        if self.start.origin_institution:
            sample.origin_institution = self.start.origin_institution
        elif hasattr(lab_test_request, 'origin_institution') and lab_test_request.origin_institution:
            sample.origin_institution = lab_test_request.origin_institution
        sample.save()
        
        # Cambiar el estado del lab test request a 'ordered'
        LabTestRequest.write([lab_test_request], {
            'state': 'ordered',
        })
        
        return 'end'