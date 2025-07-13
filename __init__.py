#!/usr/bin/env python
# -*- coding: utf-8 -*-

from trytond.pool import Pool


def register():
    from . import health_lab_workflow
    from . import lab_test_request_origin
    from . import molecular_biology
    from . import molecular_biology_wizard
    from . import histopathology
    from . import histopathology_wizard
    from . import immunoassay
    from . import immunoassay_wizard
    
    Pool.register(
        health_lab_workflow.GnuHealthLabWorkflowSample,
        health_lab_workflow.GnuHealthLab,
        health_lab_workflow.CreateLabWorkflowStart,
        lab_test_request_origin.GnuHealthPatientLabTestWithOrigin,
        lab_test_request_origin.CreateLabWorkflowStartWithOrigin,
        molecular_biology.GnuHealthLabMolecularBiology,
        molecular_biology_wizard.CreateMolecularBiologyStart,
        histopathology.GnuHealthLabHistopathology,
        histopathology.GnuHealthLabHistopathologyAntibody,
        histopathology_wizard.CreateHistopathologyStart,
        immunoassay.GnuHealthLabImmunoassay,
        immunoassay.GnuHealthLabImmunoassayAntibody,
        immunoassay_wizard.CreateImmunoassayStart,
        module='health_lab_workflow', type_='model')
    Pool.register(
        health_lab_workflow.CreateLabWorkflowWizard,
        molecular_biology_wizard.CreateMolecularBiologyWizard,
        histopathology_wizard.CreateHistopathologyWizard,
        immunoassay_wizard.CreateImmunoassayWizard,
        module='health_lab_workflow', type_='wizard')