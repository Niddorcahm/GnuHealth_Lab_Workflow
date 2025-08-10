#!/usr/bin/env python
# -*- coding: utf-8 -*-

from trytond.model import ModelView
from trytond.model import fields
from trytond.wizard import Wizard, StateView, StateTransition, Button
from trytond.transaction import Transaction
from trytond.pool import Pool
from trytond.exceptions import UserWarning
from trytond.i18n import gettext

__all__ = ['CreateLabTestFromWorkflowStart', 'CreateLabTestFromWorkflowWizard']


class CreateLabTestFromWorkflowStart(ModelView):
    'Create Lab Test from Workflow - Start'
    __name__ = 'gnuhealth.create_lab_test_from_workflow.start'
    
    # Campo informativo para mostrar en el formulario
    message = fields.Text('Information', readonly=True,
        help='Information about creating the lab test report')
    
    @staticmethod
    def default_message():
        return ('This will create a lab test report with all the criteria '
                'defined for this test type.\n\n'
                'Warning: Ensure all laboratory processes are finished '
                'before proceeding.')


class CreateLabTestFromWorkflowWizard(Wizard):
    'Create Lab Test from Workflow Sample'
    __name__ = 'gnuhealth.create_lab_test_from_workflow'
    
    start = StateView('gnuhealth.create_lab_test_from_workflow.start',
        'health_lab_workflow.create_lab_test_from_workflow_start_form', [
            Button('Cancel', 'end', 'tryton-cancel'),
            Button('Create Lab Test', 'create_lab_test', 'tryton-ok', default=True),
        ])
    create_lab_test = StateTransition()
    
    def transition_create_lab_test(self):
        pool = Pool()
        WorkflowSample = pool.get('gnuhealth.lab.workflow.sample')
        Lab = pool.get('gnuhealth.lab')
        PatientLabTest = pool.get('gnuhealth.patient.lab.test')
        
        # Obtener la muestra del workflow actual
        workflow_sample = WorkflowSample(Transaction().context['active_id'])
        
        # Verificaciones de seguridad
        if workflow_sample.state != 'completed':
            raise UserWarning('workflow_not_completed',
                'The workflow sample must be completed before creating the lab test report.')
        
        # Verificar que no exista ya un lab test con datos
        if workflow_sample.lab_test and workflow_sample.lab_test.critearea:
            raise UserWarning('lab_test_exists',
                'A lab test report already exists for this workflow sample.')
        
        # Encontrar el lab test request original
        lab_test_request = None
        
        # Buscar por el número de orden
        if workflow_sample.name:
            lab_requests = PatientLabTest.search([
                ('request', '=', workflow_sample.name),
                ('state', '=', 'ordered')
            ])
            if lab_requests:
                lab_test_request = lab_requests[0]
        
        if not lab_test_request:
            raise UserWarning('no_request_found',
                'Could not find the original lab test request for this workflow sample.')
        
        # Si ya existe un lab test pero sin criterios, lo usamos
        if workflow_sample.lab_test and not workflow_sample.lab_test.critearea:
            # Crear los criterios basados en el tipo de test
            test_cases = []
            for critearea in lab_test_request.name.critearea:
                test_cases.append(('create', [{
                    'name': critearea.name,
                    'code': critearea.code,
                    'sequence': critearea.sequence,
                    'lower_limit': critearea.lower_limit,
                    'upper_limit': critearea.upper_limit,
                    'normal_range': critearea.normal_range,
                    'units': critearea.units and critearea.units.id,
                }]))
            
            # Actualizar el lab test existente con los criterios
            Lab.write([workflow_sample.lab_test], {
                'critearea': test_cases
            })
        
        else:
            # Crear nuevo lab test completo (igual que el wizard original de health_lab)
            lab_test_data = {
                'test': lab_test_request.name.id,
                'source_type': lab_test_request.source_type,
                'patient': lab_test_request.patient_id and lab_test_request.patient_id.id,
                'other_source': lab_test_request.other_source,
                'requestor': lab_test_request.doctor_id and lab_test_request.doctor_id.id,
                'date_requested': lab_test_request.date,
                'request_order': lab_test_request.request,
            }
            
            # Copiar información del workflow si está disponible
            if workflow_sample.origin_institution:
                # Verificar si el campo existe en el modelo lab
                try:
                    lab_test_data['institution'] = workflow_sample.origin_institution.id
                except:
                    pass  # Si el campo no existe, lo ignoramos
            
            # Crear los criterios basados en el tipo de test (igual que wizard original)
            test_cases = []
            for critearea in lab_test_request.name.critearea:
                test_cases.append(('create', [{
                    'name': critearea.name,
                    'code': critearea.code,
                    'sequence': critearea.sequence,
                    'lower_limit': critearea.lower_limit,
                    'upper_limit': critearea.upper_limit,
                    'normal_range': critearea.normal_range,
                    'units': critearea.units and critearea.units.id,
                }]))
            
            lab_test_data['critearea'] = test_cases
            
            # Crear el lab test (igual que en health_lab wizard)
            lab_test = Lab.create([lab_test_data])[0]
            
            # Actualizar la muestra del workflow para referenciar el lab test
            WorkflowSample.write([workflow_sample], {
                'lab_test': lab_test.id
            })
        
        return 'end'
