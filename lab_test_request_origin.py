#!/usr/bin/env python
# -*- coding: utf-8 -*-

from trytond.pool import PoolMeta
from trytond.model import fields

__all__ = ['GnuHealthPatientLabTestWithOrigin', 'CreateLabWorkflowStartWithOrigin']


class GnuHealthPatientLabTestWithOrigin(metaclass=PoolMeta):
    'Lab Test Request with Origin Institution'
    __name__ = 'gnuhealth.patient.lab.test'
    
    # Campo de establecimiento de origen
    origin_institution = fields.Many2One('gnuhealth.institution',
        'Origin Institution',
        help='Healthcare institution where the sample was collected')


class CreateLabWorkflowStartWithOrigin(metaclass=PoolMeta):
    'Create Lab Workflow with Origin'
    __name__ = 'gnuhealth.create_lab_workflow.start'
    
    # Agregar el campo de institución de origen al wizard
    origin_institution = fields.Many2One('gnuhealth.institution',
        'Origin Institution',
        help='Healthcare institution where the sample was collected')