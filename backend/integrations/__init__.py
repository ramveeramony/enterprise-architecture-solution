"""
Enterprise Architecture Solution - Integrations Package

This package provides integration with various external systems for the Enterprise Architecture Solution.
"""

from .integration_base import IntegrationBase
from .halo_itsm import HaloITSMIntegration
from .sharepoint import SharePointIntegration
from .entra_id import EntraIDIntegration
from .microsoft_teams import TeamsIntegration
from .power_bi import PowerBIIntegration
from .visio import VisioIntegration
from .integration_manager import IntegrationManager

__all__ = [
    'IntegrationBase',
    'HaloITSMIntegration',
    'SharePointIntegration',
    'EntraIDIntegration',
    'TeamsIntegration',
    'PowerBIIntegration',
    'VisioIntegration',
    'IntegrationManager'
]
