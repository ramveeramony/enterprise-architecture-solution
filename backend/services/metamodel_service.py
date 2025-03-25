"""
Enterprise Architecture Solution - Metamodel Service

This module provides metamodel management services for the EA solution.
"""

import logging
import json
from typing import Dict, List, Any, Optional
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MetamodelService:
    """Service for managing EA metamodel entities."""
    
    def __init__(self, supabase_client):
        """Initialize the Metamodel Service.
        
        Args:
            supabase_client: A configured Supabase client for database operations
        """
        self.supabase = supabase_client
        
        # Load metamodel definitions
        self.metamodel_definitions = {
            "togaf": self._load_togaf_metamodel(),
            "archimate": self._load_archimate_metamodel(),
            "weaf": self._load_weaf_metamodel()
        }
    
    def _load_togaf_metamodel(self) -> Dict[str, Any]:
        """Load TOGAF metamodel definition.
        
        Returns:
            TOGAF metamodel dictionary
        """
        return {
            "name": "TOGAF",
            "version": "9.2",
            "domains": [
                {
                    "name": "Business",
                    "description": "Business architecture domain",
                    "element_types": [
                        {
                            "name": "Business Actor",
                            "description": "An organizational entity that is capable of performing behavior",
                            "icon": "business-actor",
                            "properties": ["resource_type", "location", "responsibilities"]
                        },
                        {
                            "name": "Business Role",
                            "description": "The responsibility for performing specific behavior",
                            "icon": "business-role",
                            "properties": ["responsibilities", "reporting_line"]
                        },
                        {
                            "name": "Business Process",
                            "description": "A behavior element that groups behavior based on an ordering of activities",
                            "icon": "business-process",
                            "properties": ["process_owner", "duration", "priority", "triggers", "outcomes"]
                        },
                        {
                            "name": "Business Function",
                            "description": "A collection of business behavior based on a set of criteria",
                            "icon": "business-function",
                            "properties": ["function_manager", "capability_level"]
                        },
                        {
                            "name": "Business Service",
                            "description": "A service that fulfills a business need for a customer",
                            "icon": "business-service",
                            "properties": ["service_owner", "service_level", "availability", "consumers"]
                        },
                        {
                            "name": "Business Object",
                            "description": "A passive element that has relevance from a business perspective",
                            "icon": "business-object",
                            "properties": ["data_classification", "retention_period", "source_of_truth"]
                        }
                    ]
                },
                {
                    "name": "Data",
                    "description": "Data architecture domain",
                    "element_types": [
                        {
                            "name": "Data Entity",
                            "description": "A fundamental data concept that cannot be further broken down",
                            "icon": "data-entity",
                            "properties": ["entity_type", "attributes", "primary_key", "data_steward"]
                        },
                        {
                            "name": "Data Component",
                            "description": "A modular, deployable, and replaceable part of a system",
                            "icon": "data-component",
                            "properties": ["component_type", "data_domains"]
                        },
                        {
                            "name": "Data Store",
                            "description": "A repository for permanently or temporarily storing data",
                            "icon": "data-store",
                            "properties": ["store_type", "capacity", "access_method", "persistence"]
                        },
                        {
                            "name": "Data Flow",
                            "description": "A directional transfer of data between nodes, processes, or applications",
                            "icon": "data-flow",
                            "properties": ["flow_type", "protocol", "frequency", "volume"]
                        }
                    ]
                },
                {
                    "name": "Application",
                    "description": "Application architecture domain",
                    "element_types": [
                        {
                            "name": "Application Component",
                            "description": "An encapsulation of application functionality aligned to implementation structure",
                            "icon": "application-component",
                            "properties": ["development_status", "lifecycle_phase", "vendor", "version"]
                        },
                        {
                            "name": "Application Interface",
                            "description": "A point of access where application services are made available to a user or another application",
                            "icon": "application-interface",
                            "properties": ["interface_type", "protocols"]
                        },
                        {
                            "name": "Application Service",
                            "description": "A service that exposes automated behavior",
                            "icon": "application-service",
                            "properties": ["service_type", "security_zone", "throughput", "response_time"]
                        },
                        {
                            "name": "Application Collaboration",
                            "description": "An aggregate of application components that work together to perform collective behavior",
                            "icon": "application-collaboration",
                            "properties": ["participant_components"]
                        }
                    ]
                },
                {
                    "name": "Technology",
                    "description": "Technology architecture domain",
                    "element_types": [
                        {
                            "name": "Node",
                            "description": "A computational resource that hosts, manipulates, or interacts with other nodes",
                            "icon": "node",
                            "properties": ["type", "environment", "location", "status"]
                        },
                        {
                            "name": "Device",
                            "description": "A physical IT resource upon which system software and artifacts may be stored or deployed",
                            "icon": "device",
                            "properties": ["manufacturer", "model", "serial_number", "purchase_date", "warranty_date"]
                        },
                        {
                            "name": "Technology Service",
                            "description": "A service that exposes technology functionality",
                            "icon": "technology-service",
                            "properties": ["service_type", "technology_standard", "performance_characteristics"]
                        },
                        {
                            "name": "Network",
                            "description": "A communication medium between two or more devices",
                            "icon": "network",
                            "properties": ["network_type", "protocol", "bandwidth", "latency"]
                        },
                        {
                            "name": "System Software",
                            "description": "Software that provides or contributes to an environment for storing, executing, and using software or data",
                            "icon": "system-software",
                            "properties": ["software_type", "license", "version", "vendor"]
                        }
                    ]
                }
            ],
            "relationship_types": [
                {
                    "name": "Composition",
                    "description": "Indicates that an element consists of one or more other concepts",
                    "directional": True
                },
                {
                    "name": "Aggregation",
                    "description": "Indicates that an element combines one or more other concepts",
                    "directional": True
                },
                {
                    "name": "Assignment",
                    "description": "Expresses the allocation of responsibility, performance of behavior, or execution",
                    "directional": True
                },
                {
                    "name": "Realization",
                    "description": "Indicates that an entity plays a critical role in the creation, achievement, or execution of a goal",
                    "directional": True
                },
                {
                    "name": "Serving",
                    "description": "Indicates that an element provides its functionality to another element",
                    "directional": True
                },
                {
                    "name": "Access",
                    "description": "Indicates the ability of a behavior element to observe or act upon a passive element",
                    "directional": True
                },
                {
                    "name": "Influence",
                    "description": "Indicates that an element affects the implementation, operation, or behavior of another element",
                    "directional": True
                },
                {
                    "name": "Association",
                    "description": "Indicates a relationship between elements with unspecified directionality and meaning",
                    "directional": False
                },
                {
                    "name": "Flow",
                    "description": "Represents transfer from one element to another",
                    "directional": True
                }
            ]
        }
    
    def _load_archimate_metamodel(self) -> Dict[str, Any]:
        """Load ArchiMate metamodel definition.
        
        Returns:
            ArchiMate metamodel dictionary
        """
        return {
            "name": "ArchiMate",
            "version": "3.1",
            "domains": [
                {
                    "name": "Strategy",
                    "description": "Strategy architecture domain",
                    "element_types": [
                        {
                            "name": "Resource",
                            "description": "An asset owned or controlled by an individual or organization",
                            "icon": "resource",
                            "properties": ["resource_type", "owner", "value", "strategic_importance"]
                        },
                        {
                            "name": "Capability",
                            "description": "An ability that an active structure element possesses",
                            "icon": "capability",
                            "properties": ["maturity_level", "criticality", "growth_potential"]
                        },
                        {
                            "name": "Value Stream",
                            "description": "A sequence of activities that create an overall result for a customer, stakeholder, or end user",
                            "icon": "value-stream",
                            "properties": ["trigger", "outcome", "value_proposition", "kpis"]
                        },
                        {
                            "name": "Course of Action",
                            "description": "An approach or plan for configuring some capabilities and resources",
                            "icon": "course-of-action",
                            "properties": ["time_frame", "investment_size", "risk_level", "expected_outcomes"]
                        }
                    ]
                },
                {
                    "name": "Business",
                    "description": "Business architecture domain",
                    "element_types": [
                        {
                            "name": "Business Actor",
                            "description": "An organizational entity that is capable of performing behavior",
                            "icon": "business-actor",
                            "properties": ["resource_type", "location", "responsibilities"]
                        },
                        {
                            "name": "Business Role",
                            "description": "The responsibility for performing specific behavior",
                            "icon": "business-role",
                            "properties": ["responsibilities", "reporting_line"]
                        },
                        {
                            "name": "Business Process",
                            "description": "A behavior element that groups behavior based on an ordering of activities",
                            "icon": "business-process",
                            "properties": ["process_owner", "duration", "priority", "triggers", "outcomes"]
                        },
                        {
                            "name": "Business Function",
                            "description": "A collection of business behavior based on a set of criteria",
                            "icon": "business-function",
                            "properties": ["function_manager", "capability_level"]
                        },
                        {
                            "name": "Business Service",
                            "description": "A service that fulfills a business need for a customer",
                            "icon": "business-service",
                            "properties": ["service_owner", "service_level", "availability", "consumers"]
                        },
                        {
                            "name": "Business Object",
                            "description": "A passive element that has relevance from a business perspective",
                            "icon": "business-object",
                            "properties": ["data_classification", "retention_period", "source_of_truth"]
                        },
                        {
                            "name": "Contract",
                            "description": "A formal or informal specification of an agreement",
                            "icon": "contract",
                            "properties": ["validity_period", "conditions", "parties_involved"]
                        },
                        {
                            "name": "Representation",
                            "description": "A perceptible form of the information carried by a business object",
                            "icon": "representation",
                            "properties": ["format", "medium", "accessibility"]
                        }
                    ]
                },
                {
                    "name": "Application",
                    "description": "Application architecture domain",
                    "element_types": [
                        {
                            "name": "Application Component",
                            "description": "An encapsulation of application functionality aligned to implementation structure",
                            "icon": "application-component",
                            "properties": ["development_status", "lifecycle_phase", "vendor", "version"]
                        },
                        {
                            "name": "Application Interface",
                            "description": "A point of access where application services are made available to a user or another application",
                            "icon": "application-interface",
                            "properties": ["interface_type", "protocols"]
                        },
                        {
                            "name": "Application Service",
                            "description": "A service that exposes automated behavior",
                            "icon": "application-service",
                            "properties": ["service_type", "security_zone", "throughput", "response_time"]
                        },
                        {
                            "name": "Application Collaboration",
                            "description": "An aggregate of application components that work together to perform collective behavior",
                            "icon": "application-collaboration",
                            "properties": ["participant_components"]
                        },
                        {
                            "name": "Data Object",
                            "description": "Data structured for automated processing",
                            "icon": "data-object",
                            "properties": ["data_type", "structure", "volume", "retention"]
                        }
                    ]
                },
                {
                    "name": "Technology",
                    "description": "Technology architecture domain",
                    "element_types": [
                        {
                            "name": "Node",
                            "description": "A computational resource that hosts, manipulates, or interacts with other nodes",
                            "icon": "node",
                            "properties": ["type", "environment", "location", "status"]
                        },
                        {
                            "name": "Device",
                            "description": "A physical IT resource upon which system software and artifacts may be stored or deployed",
                            "icon": "device",
                            "properties": ["manufacturer", "model", "serial_number", "purchase_date", "warranty_date"]
                        },
                        {
                            "name": "Technology Service",
                            "description": "A service that exposes technology functionality",
                            "icon": "technology-service",
                            "properties": ["service_type", "technology_standard", "performance_characteristics"]
                        },
                        {
                            "name": "Network",
                            "description": "A communication medium between two or more devices",
                            "icon": "network",
                            "properties": ["network_type", "protocol", "bandwidth", "latency"]
                        },
                        {
                            "name": "System Software",
                            "description": "Software that provides or contributes to an environment for storing, executing, and using software or data",
                            "icon": "system-software",
                            "properties": ["software_type", "license", "version", "vendor"]
                        },
                        {
                            "name": "Technology Interface",
                            "description": "A point of access where technology services are made available",
                            "icon": "technology-interface",
                            "properties": ["interface_type", "connection_type", "protocols"]
                        },
                        {
                            "name": "Artifact",
                            "description": "A physical piece of data that is used or produced in a software development process",
                            "icon": "artifact",
                            "properties": ["artifact_type", "file_type", "size", "location"]
                        }
                    ]
                },
                {
                    "name": "Physical",
                    "description": "Physical architecture domain",
                    "element_types": [
                        {
                            "name": "Equipment",
                            "description": "One or more physical machines, tools, or instruments",
                            "icon": "equipment",
                            "properties": ["equipment_type", "manufacturer", "model", "location"]
                        },
                        {
                            "name": "Facility",
                            "description": "A physical structure or environment",
                            "icon": "facility",
                            "properties": ["facility_type", "address", "area", "capacity"]
                        },
                        {
                            "name": "Distribution Network",
                            "description": "A physical network used to transport materials or energy",
                            "icon": "distribution-network",
                            "properties": ["network_type", "coverage", "capacity"]
                        },
                        {
                            "name": "Material",
                            "description": "A tangible physical element",
                            "icon": "material",
                            "properties": ["material_type", "composition", "quantity"]
                        }
                    ]
                },
                {
                    "name": "Implementation",
                    "description": "Implementation and migration domain",
                    "element_types": [
                        {
                            "name": "Work Package",
                            "description": "A series of actions identified and designed to achieve specific results",
                            "icon": "work-package",
                            "properties": ["start_date", "end_date", "resources", "deliverables", "dependencies"]
                        },
                        {
                            "name": "Deliverable",
                            "description": "A precisely-defined outcome of a work package",
                            "icon": "deliverable",
                            "properties": ["deliverable_type", "acceptance_criteria", "due_date"]
                        },
                        {
                            "name": "Plateau",
                            "description": "A relatively stable state of the architecture that exists during a limited period of time",
                            "icon": "plateau",
                            "properties": ["start_date", "end_date", "stability_criteria"]
                        },
                        {
                            "name": "Gap",
                            "description": "A statement of difference between two plateaus",
                            "icon": "gap",
                            "properties": ["gap_type", "impact", "resolution_approach"]
                        }
                    ]
                }
            ],
            "relationship_types": [
                {
                    "name": "Composition",
                    "description": "Indicates that an element consists of one or more other concepts",
                    "directional": True
                },
                {
                    "name": "Aggregation",
                    "description": "Indicates that an element combines one or more other concepts",
                    "directional": True
                },
                {
                    "name": "Assignment",
                    "description": "Expresses the allocation of responsibility, performance of behavior, or execution",
                    "directional": True
                },
                {
                    "name": "Realization",
                    "description": "Indicates that an entity plays a critical role in the creation, achievement, or execution of a goal",
                    "directional": True
                },
                {
                    "name": "Serving",
                    "description": "Indicates that an element provides its functionality to another element",
                    "directional": True
                },
                {
                    "name": "Access",
                    "description": "Indicates the ability of a behavior element to observe or act upon a passive element",
                    "directional": True
                },
                {
                    "name": "Influence",
                    "description": "Indicates that an element affects the implementation, operation, or behavior of another element",
                    "directional": True
                },
                {
                    "name": "Association",
                    "description": "Indicates a relationship between elements with unspecified directionality and meaning",
                    "directional": False
                },
                {
                    "name": "Flow",
                    "description": "Represents transfer from one element to another",
                    "directional": True
                },
                {
                    "name": "Triggering",
                    "description": "Describes a temporal or causal relationship between elements",
                    "directional": True
                },
                {
                    "name": "Specialization",
                    "description": "Indicates that an element is a particular kind of another element",
                    "directional": True
                }
            ]
        }
    
    def _load_weaf_metamodel(self) -> Dict[str, Any]:
        """Load WA Enterprise Architecture Framework (WEAF) metamodel definition.
        
        Returns:
            WEAF metamodel dictionary
        """
        return {
            "name": "WEAF",
            "version": "1.0",
            "domains": [
                {
                    "name": "Performance",
                    "description": "Performance architecture domain",
                    "element_types": [
                        {
                            "name": "Strategic Outcome",
                            "description": "A high-level goal that describes the desired end result to be achieved",
                            "icon": "strategic-outcome",
                            "properties": ["priority", "target_date", "success_measures", "stakeholders", "alignment"]
                        },
                        {
                            "name": "KPI",
                            "description": "Key Performance Indicator that measures progress toward strategic outcomes",
                            "icon": "kpi",
                            "properties": ["metric_type", "target_value", "current_value", "measurement_frequency", "data_source"]
                        },
                        {
                            "name": "Benefit",
                            "description": "A measurable improvement resulting from an outcome that is perceived as positive by a stakeholder",
                            "icon": "benefit",
                            "properties": ["benefit_type", "value", "timeline", "beneficiaries"]
                        },
                        {
                            "name": "Risk",
                            "description": "An uncertain event or condition that, if it occurs, has a positive or negative effect on objectives",
                            "icon": "risk",
                            "properties": ["risk_type", "probability", "impact", "mitigation_strategy", "risk_owner"]
                        }
                    ]
                },
                {
                    "name": "Business",
                    "description": "Business architecture domain",
                    "element_types": [
                        {
                            "name": "Business Capability",
                            "description": "An ability that an organization may have or exchange to achieve a specific purpose or outcome",
                            "icon": "business-capability",
                            "properties": ["capability_level", "maturity", "criticality", "owner", "growth_strategy"]
                        },
                        {
                            "name": "Business Function",
                            "description": "A collection of business behavior based on a set of criteria",
                            "icon": "business-function",
                            "properties": ["function_manager", "capability_level"]
                        },
                        {
                            "name": "Business Process",
                            "description": "A behavior element that groups behavior based on an ordering of activities",
                            "icon": "business-process",
                            "properties": ["process_owner", "duration", "priority", "triggers", "outcomes"]
                        },
                        {
                            "name": "Business Service",
                            "description": "A service that fulfills a business need for a customer",
                            "icon": "business-service",
                            "properties": ["service_owner", "service_level", "availability", "consumers"]
                        },
                        {
                            "name": "Organization Unit",
                            "description": "A part of an organization that has responsibility for a specific set of capabilities or functions",
                            "icon": "organization-unit",
                            "properties": ["unit_type", "head_count", "locations", "reporting_line"]
                        },
                        {
                            "name": "Stakeholder",
                            "description": "An individual, group, or organization with an interest in or concerns about aspects of the architecture",
                            "icon": "stakeholder",
                            "properties": ["stakeholder_type", "influence_level", "interest_level", "engagement_approach"]
                        }
                    ]
                },
                {
                    "name": "Services",
                    "description": "Services architecture domain",
                    "element_types": [
                        {
                            "name": "Digital Service",
                            "description": "A service delivered through digital channels to address customer needs",
                            "icon": "digital-service",
                            "properties": ["service_type", "delivery_channels", "target_users", "accessibility_level"]
                        },
                        {
                            "name": "Service Proposition",
                            "description": "The value offered by a service to meet specific customer needs",
                            "icon": "service-proposition",
                            "properties": ["value_elements", "target_segments", "differentiation", "pricing_model"]
                        },
                        {
                            "name": "Service Channel",
                            "description": "A means through which services are delivered to customers",
                            "icon": "service-channel",
                            "properties": ["channel_type", "availability", "accessibility", "cost_to_serve"]
                        },
                        {
                            "name": "Service Level",
                            "description": "An agreed standard of service quality for a particular service",
                            "icon": "service-level",
                            "properties": ["performance_metrics", "target_values", "priority", "review_frequency"]
                        },
                        {
                            "name": "Service Journey",
                            "description": "The end-to-end experience of a customer when using a service",
                            "icon": "service-journey",
                            "properties": ["journey_stages", "touchpoints", "pain_points", "moments_of_truth"]
                        }
                    ]
                },
                {
                    "name": "Data",
                    "description": "Data architecture domain",
                    "element_types": [
                        {
                            "name": "Data Entity",
                            "description": "A fundamental data concept that cannot be further broken down",
                            "icon": "data-entity",
                            "properties": ["entity_type", "attributes", "primary_key", "data_steward"]
                        },
                        {
                            "name": "Data Store",
                            "description": "A repository for permanently or temporarily storing data",
                            "icon": "data-store",
                            "properties": ["store_type", "capacity", "access_method", "persistence"]
                        },
                        {
                            "name": "Data Flow",
                            "description": "A directional transfer of data between nodes, processes, or applications",
                            "icon": "data-flow",
                            "properties": ["flow_type", "protocol", "frequency", "volume"]
                        },
                        {
                            "name": "Data Standard",
                            "description": "A rule or guideline for the way data is described and recorded",
                            "icon": "data-standard",
                            "properties": ["standard_type", "compliance_level", "governing_body", "review_cycle"]
                        },
                        {
                            "name": "Information Product",
                            "description": "A packaged collection of information for consumption by stakeholders",
                            "icon": "information-product",
                            "properties": ["product_type", "audience", "delivery_mechanism", "update_frequency"]
                        }
                    ]
                },
                {
                    "name": "Technology",
                    "description": "Technology architecture domain",
                    "element_types": [
                        {
                            "name": "Application",
                            "description": "A deployed and operational IT system that supports business functions and services",
                            "icon": "application",
                            "properties": ["app_type", "lifecycle_stage", "criticality", "owner", "vendor", "version"]
                        },
                        {
                            "name": "Technology Component",
                            "description": "A modular part of a technology platform with defined interfaces",
                            "icon": "technology-component",
                            "properties": ["component_type", "technology_stack", "reusability", "maintainability"]
                        },
                        {
                            "name": "Technology Service",
                            "description": "A service that exposes technology functionality",
                            "icon": "technology-service",
                            "properties": ["service_type", "technology_standard", "performance_characteristics"]
                        },
                        {
                            "name": "Platform",
                            "description": "A collection of technology components that provides the foundation for delivering applications",
                            "icon": "platform",
                            "properties": ["platform_type", "hosting_model", "scalability", "elasticity"]
                        },
                        {
                            "name": "Infrastructure Node",
                            "description": "A computational resource that hosts applications and technology components",
                            "icon": "infrastructure-node",
                            "properties": ["node_type", "environment", "location", "capacity", "redundancy"]
                        },
                        {
                            "name": "Security Control",
                            "description": "A safeguard or countermeasure to avoid, detect, counteract, or minimize security risks",
                            "icon": "security-control",
                            "properties": ["control_type", "protection_level", "compliance_standards", "verification_method"]
                        }
                    ]
                }
            ],
            "relationship_types": [
                {
                    "name": "Composition",
                    "description": "Indicates that an element consists of one or more other concepts",
                    "directional": True
                },
                {
                    "name": "Aggregation",
                    "description": "Indicates that an element combines one or more other concepts",
                    "directional": True
                },
                {
                    "name": "Assignment",
                    "description": "Expresses the allocation of responsibility, performance of behavior, or execution",
                    "directional": True
                },
                {
                    "name": "Realization",
                    "description": "Indicates that an entity plays a critical role in the creation, achievement, or execution of a goal",
                    "directional": True
                },
                {
                    "name": "Serving",
                    "description": "Indicates that an element provides its functionality to another element",
                    "directional": True
                },
                {
                    "name": "Access",
                    "description": "Indicates the ability of a behavior element to observe or act upon a passive element",
                    "directional": True
                },
                {
                    "name": "Influence",
                    "description": "Indicates that an element affects the implementation, operation, or behavior of another element",
                    "directional": True
                },
                {
                    "name": "Association",
                    "description": "Indicates a relationship between elements with unspecified directionality and meaning",
                    "directional": False
                },
                {
                    "name": "Flow",
                    "description": "Represents transfer from one element to another",
                    "directional": True
                },
                {
                    "name": "Supports",
                    "description": "Indicates that an element provides support for another element",
                    "directional": True
                },
                {
                    "name": "Delivers",
                    "description": "Indicates that an element plays a role in the delivery of another element",
                    "directional": True
                },
                {
                    "name": "Measures",
                    "description": "Indicates that an element provides a measurement of another element",
                    "directional": True
                }
            ]
        }
    
    def get_available_frameworks(self) -> List[Dict[str, Any]]:
        """Get a list of available architectural frameworks.
        
        Returns:
            List of available architectural frameworks
        """
        frameworks = []
        for framework_id, framework in self.metamodel_definitions.items():
            frameworks.append({
                "id": framework_id,
                "name": framework["name"],
                "version": framework["version"]
            })
        
        return frameworks
    
    def get_framework(self, framework_id: str) -> Optional[Dict[str, Any]]:
        """Get detailed information about a specific architectural framework.
        
        Args:
            framework_id: ID of the framework
            
        Returns:
            Framework information or None if not found
        """
        if framework_id in self.metamodel_definitions:
            return self.metamodel_definitions[framework_id]
        else:
            return None
    
    def get_element_types_for_framework(self, framework_id: str, domain_name: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get element types defined in a framework, optionally filtered by domain.
        
        Args:
            framework_id: ID of the framework
            domain_name: Optional name of the domain to filter by
            
        Returns:
            List of element types
        """
        if framework_id not in self.metamodel_definitions:
            return []
        
        framework = self.metamodel_definitions[framework_id]
        element_types = []
        
        for domain in framework["domains"]:
            if domain_name and domain["name"] != domain_name:
                continue
                
            for element_type in domain["element_types"]:
                element_types.append({
                    "name": element_type["name"],
                    "description": element_type["description"],
                    "icon": element_type["icon"],
                    "domain": domain["name"],
                    "properties": element_type["properties"]
                })
        
        return element_types
    
    def get_relationship_types_for_framework(self, framework_id: str) -> List[Dict[str, Any]]:
        """Get relationship types defined in a framework.
        
        Args:
            framework_id: ID of the framework
            
        Returns:
            List of relationship types
        """
        if framework_id not in self.metamodel_definitions:
            return []
        
        framework = self.metamodel_definitions[framework_id]
        return framework["relationship_types"]
    
    def apply_framework_to_model(self, model_id: str, framework_id: str, user_id: str) -> bool:
        """Apply a metamodel framework to an existing EA model.
        
        Args:
            model_id: UUID of the model
            framework_id: ID of the framework to apply
            user_id: UUID of the user applying the framework
            
        Returns:
            True if successful, False otherwise
        """
        try:
            if framework_id not in self.metamodel_definitions:
                return False
            
            framework = self.metamodel_definitions[framework_id]
            
            # Get the model
            model_result = self.supabase.table("ea_models").select("*").eq("id", model_id).single().execute()
            if not model_result.data:
                return False
            
            model = model_result.data
            
            # Update model properties with framework information
            properties = model.get("properties", {})
            if not properties:
                properties = {}
                
            properties["framework"] = {
                "id": framework_id,
                "name": framework["name"],
                "version": framework["version"],
                "applied_at": datetime.now().isoformat(),
                "applied_by": user_id
            }
            
            # Update the model
            self.supabase.table("ea_models").update({"properties": properties}).eq("id", model_id).execute()
            
            # Create domains if they don't exist
            for domain in framework["domains"]:
                domain_result = self.supabase.table("ea_domains").select("*").eq("name", domain["name"]).execute()
                
                if not domain_result.data:
                    # Create the domain
                    self.supabase.table("ea_domains").insert({
                        "name": domain["name"],
                        "description": domain["description"],
                        "created_at": datetime.now().isoformat()
                    }).execute()
            
            # Get all domain IDs
            domains_result = self.supabase.table("ea_domains").select("*").execute()
            domains = {domain["name"]: domain["id"] for domain in domains_result.data}
            
            # Create element types for each domain
            for domain in framework["domains"]:
                if domain["name"] not in domains:
                    continue
                    
                domain_id = domains[domain["name"]]
                
                for element_type in domain["element_types"]:
                    # Check if element type already exists
                    element_type_result = self.supabase.table("ea_element_types").select("*").eq("name", element_type["name"]).eq("domain_id", domain_id).execute()
                    
                    if not element_type_result.data:
                        # Create the element type
                        self.supabase.table("ea_element_types").insert({
                            "domain_id": domain_id,
                            "name": element_type["name"],
                            "description": element_type["description"],
                            "icon": element_type.get("icon"),
                            "properties": {"standard_properties": element_type.get("properties", [])},
                            "created_at": datetime.now().isoformat()
                        }).execute()
            
            # Create relationship types
            for relationship_type in framework["relationship_types"]:
                # Check if relationship type already exists
                relationship_type_result = self.supabase.table("ea_relationship_types").select("*").eq("name", relationship_type["name"]).execute()
                
                if not relationship_type_result.data:
                    # Create the relationship type
                    self.supabase.table("ea_relationship_types").insert({
                        "name": relationship_type["name"],
                        "description": relationship_type["description"],
                        "directional": relationship_type["directional"],
                        "created_at": datetime.now().isoformat()
                    }).execute()
            
            return True
            
        except Exception as e:
            logger.error(f"Error applying framework to model: {str(e)}")
            return False
    
    def validate_element_against_framework(self, element_data: Dict[str, Any], framework_id: str) -> Dict[str, Any]:
        """Validate an element against a framework's metamodel.
        
        Args:
            element_data: Element data to validate
            framework_id: ID of the framework
            
        Returns:
            Dictionary with validation results
        """
        if framework_id not in self.metamodel_definitions:
            return {"valid": False, "errors": ["Framework not found"]}
        
        framework = self.metamodel_definitions[framework_id]
        errors = []
        
        # Get the element type
        element_type_result = self.supabase.table("ea_element_types").select("*, ea_domains(name)").eq("id", element_data.get("type_id")).single().execute()
        
        if not element_type_result.data:
            return {"valid": False, "errors": ["Element type not found"]}
        
        element_type = element_type_result.data
        domain_name = element_type["ea_domains"]["name"]
        
        # Find the corresponding domain and element type in the framework
        framework_element_type = None
        for domain in framework["domains"]:
            if domain["name"] == domain_name:
                for et in domain["element_types"]:
                    if et["name"] == element_type["name"]:
                        framework_element_type = et
                        break
                if framework_element_type:
                    break
        
        if not framework_element_type:
            return {"valid": False, "errors": [f"Element type '{element_type['name']}' not defined in framework for domain '{domain_name}'"]}
        
        # Validate properties against framework
        standard_properties = framework_element_type.get("properties", [])
        element_properties = element_data.get("properties", {})
        
        for prop in standard_properties:
            if prop not in element_properties:
                errors.append(f"Missing property '{prop}' defined in framework")
        
        # Return validation results
        return {
            "valid": len(errors) == 0,
            "errors": errors,
            "warnings": [],
            "framework_element_type": framework_element_type
        }
    
    def validate_relationship_against_framework(self, relationship_data: Dict[str, Any], framework_id: str) -> Dict[str, Any]:
        """Validate a relationship against a framework's metamodel.
        
        Args:
            relationship_data: Relationship data to validate
            framework_id: ID of the framework
            
        Returns:
            Dictionary with validation results
        """
        if framework_id not in self.metamodel_definitions:
            return {"valid": False, "errors": ["Framework not found"]}
        
        framework = self.metamodel_definitions[framework_id]
        errors = []
        
        # Get the relationship type
        relationship_type_result = self.supabase.table("ea_relationship_types").select("*").eq("id", relationship_data.get("relationship_type_id")).single().execute()
        
        if not relationship_type_result.data:
            return {"valid": False, "errors": ["Relationship type not found"]}
        
        relationship_type = relationship_type_result.data
        
        # Find the corresponding relationship type in the framework
        framework_relationship_type = None
        for rt in framework["relationship_types"]:
            if rt["name"] == relationship_type["name"]:
                framework_relationship_type = rt
                break
        
        if not framework_relationship_type:
            return {"valid": False, "errors": [f"Relationship type '{relationship_type['name']}' not defined in framework"]}
        
        # Check if the source and target elements are valid for this relationship
        source_element_result = self.supabase.table("ea_elements").select("*, ea_element_types(name, domain_id, ea_domains(name))").eq("id", relationship_data.get("source_element_id")).single().execute()
        target_element_result = self.supabase.table("ea_elements").select("*, ea_element_types(name, domain_id, ea_domains(name))").eq("id", relationship_data.get("target_element_id")).single().execute()
        
        if not source_element_result.data or not target_element_result.data:
            return {"valid": False, "errors": ["Source or target element not found"]}
        
        source_element = source_element_result.data
        target_element = target_element_result.data
        
        # Return validation results
        return {
            "valid": len(errors) == 0,
            "errors": errors,
            "warnings": [],
            "framework_relationship_type": framework_relationship_type
        }
