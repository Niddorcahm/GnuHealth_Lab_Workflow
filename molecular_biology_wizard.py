#!/usr/bin/env python
# -*- coding: utf-8 -*-

from trytond.model import ModelView, fields
from trytond.wizard import Wizard, StateView, StateTransition, Button
from trytond.pool import Pool
from trytond.transaction import Transaction
from trytond.exceptions import UserWarning

__all__ = ['CreateMolecularBiologyStart', 'CreateMolecularBiologyWizard']


class CreateMolecularBiologyStart(ModelView):
    'Create Molecular Biology Process'
    __name__ = 'gnuhealth.create_molecular_biology.start'
    
    study_type = fields.Selection([
        ('pcr_endpoint', 'PCR Endpoint'),
        ('qpcr', 'qPCR (Real-time PCR)'),
        ('rt_pcr', 'RT-PCR'),
        ('sequencing', 'Sequencing'),
        ('extraction_only', 'Genetic Material Extraction Only'),
        ('electrophoresis', 'Protein Electrophoresis'),
    ], 'Study Type', required=True,
    help='Type of molecular biology study')
    
    responsible_professional = fields.Many2One('gnuhealth.healthprofessional',
        'Responsible Professional', required=True,
        help='Professional responsible for the complete process')
    
    observations = fields.Text('Initial Observations')
    
    @staticmethod
    def default_study_type():
        return 'pcr_endpoint'


class CreateMolecularBiologyWizard(Wizard):
    'Create Molecular Biology Process'
    __name__ = 'gnuhealth.create_molecular_biology'
    
    start = StateView('gnuhealth.create_molecular_biology.start',
        'health_lab_workflow.create_molecular_biology_start_form', [
            Button('Cancel', 'end', 'tryton-cancel'),
            Button('Create', 'create_process', 'tryton-ok', default=True),
        ])
    create_process = StateTransition()
    
    def transition_create_process(self):
        pool = Pool()
        WorkflowSample = pool.get('gnuhealth.lab.workflow.sample')
        MolecularBiology = pool.get('gnuhealth.lab.molecular_biology')
        
        # Obtener la muestra del workflow actual
        workflow_sample = WorkflowSample(Transaction().context['active_id'])
        
        # Verificar que no exista un proceso activo
        existing = MolecularBiology.search([
            ('workflow_sample', '=', workflow_sample.id),
            ('state', 'in', ['draft', 'in_progress']),
        ])
        
        if existing:
            raise UserWarning('molecular_exists',
                'An active molecular biology process already exists for this sample.')
        
        # Crear el proceso de biología molecular
        molecular_process = MolecularBiology()
        molecular_process.workflow_sample = workflow_sample
        molecular_process.study_type = self.start.study_type
        molecular_process.responsible_professional = self.start.responsible_professional
        molecular_process.observations = self.start.observations
        molecular_process.save()
        
        # Si la muestra está en 'received', cambiarla a 'processing'
        if workflow_sample.state == 'received':
            WorkflowSample.process([workflow_sample])
        
        return 'end'