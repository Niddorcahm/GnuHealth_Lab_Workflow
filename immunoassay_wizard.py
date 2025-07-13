#!/usr/bin/env python
# -*- coding: utf-8 -*-

from trytond.model import ModelView, fields
from trytond.wizard import Wizard, StateView, StateTransition, Button
from trytond.pool import Pool
from trytond.transaction import Transaction
from trytond.exceptions import UserWarning

__all__ = ['CreateImmunoassayStart', 'CreateImmunoassayWizard']


class CreateImmunoassayStart(ModelView):
    'Create Immunoassay Process'
    __name__ = 'gnuhealth.create_immunoassay.start'
    
    assay_type = fields.Selection([
        ('elisa', 'ELISA (Enzyme-Linked Immunosorbent Assay)'),
        ('clia', 'CLIA (Chemiluminescent Immunoassay)'),
    ], 'Assay Type', required=True,
    help='Type of immunoassay')
    
    kit_name = fields.Char('Kit Name', required=True,
        help='Commercial kit name and manufacturer')
    
    kit_lot = fields.Char('Kit Lot Number',
        help='Lot number of the kit used')
    
    responsible_professional = fields.Many2One('gnuhealth.healthprofessional',
        'Responsible Professional', required=True,
        help='Professional responsible for the complete process')
    
    observations = fields.Text('Initial Observations')
    
    @staticmethod
    def default_assay_type():
        return 'elisa'


class CreateImmunoassayWizard(Wizard):
    'Create Immunoassay Process'
    __name__ = 'gnuhealth.create_immunoassay'
    
    start = StateView('gnuhealth.create_immunoassay.start',
        'health_lab_workflow.create_immunoassay_start_form', [
            Button('Cancel', 'end', 'tryton-cancel'),
            Button('Create', 'create_process', 'tryton-ok', default=True),
        ])
    create_process = StateTransition()
    
    def transition_create_process(self):
        pool = Pool()
        WorkflowSample = pool.get('gnuhealth.lab.workflow.sample')
        Immunoassay = pool.get('gnuhealth.lab.immunoassay')
        
        # Obtener la muestra del workflow actual
        workflow_sample = WorkflowSample(Transaction().context['active_id'])
        
        # Verificar que no exista un proceso activo
        existing = Immunoassay.search([
            ('workflow_sample', '=', workflow_sample.id),
            ('state', 'in', ['draft', 'in_progress']),
        ])
        
        if existing:
            raise UserWarning('immunoassay_exists',
                'An active immunoassay process already exists for this sample.')
        
        # Crear el proceso de inmunoensayo
        immunoassay_process = Immunoassay()
        immunoassay_process.workflow_sample = workflow_sample
        immunoassay_process.assay_type = self.start.assay_type
        immunoassay_process.kit_name = self.start.kit_name
        immunoassay_process.kit_lot = self.start.kit_lot
        immunoassay_process.responsible_professional = self.start.responsible_professional
        immunoassay_process.observations = self.start.observations
        immunoassay_process.save()
        
        # Si la muestra está en 'received', cambiarla a 'processing'
        if workflow_sample.state == 'received':
            WorkflowSample.process([workflow_sample])
        
        return 'end'