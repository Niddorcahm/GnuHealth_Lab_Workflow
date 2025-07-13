#!/usr/bin/env python
# -*- coding: utf-8 -*-

from trytond.model import ModelView, fields
from trytond.wizard import Wizard, StateView, StateTransition, Button
from trytond.pool import Pool
from trytond.transaction import Transaction
from trytond.exceptions import UserWarning

__all__ = ['CreateHistopathologyStart', 'CreateHistopathologyWizard']


class CreateHistopathologyStart(ModelView):
    'Create Histopathology Process'
    __name__ = 'gnuhealth.create_histopathology.start'
    
    study_type = fields.Selection([
        ('routine', 'Routine Histopathology'),
        ('histochemistry', 'Histochemistry'),
        ('immunohistochemistry', 'Immunohistochemistry'),
        ('fish', 'FISH (Fluorescence In Situ Hybridization)'),
        ('cytology', 'Cytology'),
    ], 'Study Type', required=True,
    help='Type of histopathology study')
    
    responsible_professional = fields.Many2One('gnuhealth.healthprofessional',
        'Responsible Professional', required=True,
        help='Professional responsible for the complete process')
    
    observations = fields.Text('Initial Observations')
    
    @staticmethod
    def default_study_type():
        return 'routine'


class CreateHistopathologyWizard(Wizard):
    'Create Histopathology Process'
    __name__ = 'gnuhealth.create_histopathology'
    
    start = StateView('gnuhealth.create_histopathology.start',
        'health_lab_workflow.create_histopathology_start_form', [
            Button('Cancel', 'end', 'tryton-cancel'),
            Button('Create', 'create_process', 'tryton-ok', default=True),
        ])
    create_process = StateTransition()
    
    def transition_create_process(self):
        pool = Pool()
        WorkflowSample = pool.get('gnuhealth.lab.workflow.sample')
        Histopathology = pool.get('gnuhealth.lab.histopathology')
        
        # Obtener la muestra del workflow actual
        workflow_sample = WorkflowSample(Transaction().context['active_id'])
        
        # Verificar que no exista un proceso activo
        existing = Histopathology.search([
            ('workflow_sample', '=', workflow_sample.id),
            ('state', 'in', ['draft', 'macroscopy', 'processing', 
                           'cutting', 'staining']),
        ])
        
        if existing:
            raise UserWarning('histopathology_exists',
                'An active histopathology process already exists for this sample.')
        
        # Crear el proceso de histopatología
        histopathology_process = Histopathology()
        histopathology_process.workflow_sample = workflow_sample
        histopathology_process.study_type = self.start.study_type
        histopathology_process.responsible_professional = self.start.responsible_professional
        histopathology_process.observations = self.start.observations
        histopathology_process.save()
        
        # Si la muestra está en 'received', cambiarla a 'processing'
        if workflow_sample.state == 'received':
            WorkflowSample.process([workflow_sample])
        
        return 'end'