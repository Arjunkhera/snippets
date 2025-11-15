### Query to search for documents under a specific client.

```json
{
    "bool": {
        "must": [
            {
                "term": {
                    "entityType.keyword": "FOLDER"
                }
            },
            {
                "term": {
                    "commonAttributes.applicationAttributes.relationshipId.keyword": "9341455527283258"
                }
            },
            {
                "term": {
                    "commonAttributes.applicationAttributes.relationshipType.keyword": "client"
                }
            },
            {
                "term": {
                    "commonAttributes.applicationAttributes.category.keyword": "_private.qboa"
                }
            },
            {
                "term": {
                    "authorization.isPci": false
                }
            },
            {
                "term": {
                    "commonAttributes.taxYear.keyword": 2024
                }
            },
            {
                "term": {
                    "commonAttributes.applicationAttributes.subcategory.keyword": "booksreview"
                }
            }
        ]
    }
}
```

### Query to search for documents under a specific folder.

```json
{
    "bool": {
        "should": [
            {
                "bool": {
                    "must": [
                        {
                            "term": {
                                "entityType.keyword": "DOCUMENT"
                            }
                        },
                        {
                            "term": {
                                "systemAttributes.parentId.keyword": "40658d40-8764-4b41-aea6-a6c6450944e6"
                            }
                        }
                    ]
                }
            },
            {
                "bool": {
                    "must": [
                        {
                            "term": {
                                "entityType.keyword": "FOLDER"
                            }
                        },
                        {
                            "term": {
                                "systemAttributes.parentId.keyword": "40658d40-8764-4b41-aea6-a6c6450944e6"
                            }
                        }
                    ]
                }
            }
        ]
    }
}
```


### Query to search for documents that have a specific offering ID.

```json
{
    "bool": {
        "filter": [
            {
                "terms": {
                    "systemAttributes.offeringId.keyword": [
                        "Intuit.smallbusiness.qbeswarehouse.qbwhandroidapp",
                        "Intuit.qbshared.attachments.qbdtreceiptscapturemob",
                        "Intuit.qbshared.attachments.qbdtreceiptscapture"
                    ]
                }
            }
        ],
        "must": [
            {
                "term": {
                    "commonAttributes.documentType.keyword": "receipt"
                }
            },
            {
                "term": {
                    "authorization.authType.keyword": "REALM"
                }
            }
        ],
        "must_not": [
            {
                "term": {
                    "commonAttributes.applicationAttributes.category.keyword": "reviewed"
                }
            },
            {
                "term": {
                    "systemAttributes.dataExtractionStatus.keyword": "ASYNC_COMPLETED"
                }
            }
        ]
    }
}
```

### Query to list documents under root folder.

```json
{
    "bool": {
        "should": [
            {
                "bool": {
                    "must": [
                        {
                            "term": {
                                "entityType.keyword": "DOCUMENT"
                            }
                        },
                        {
                            "term": {
                                "systemAttributes.parentId.keyword": "root"
                            }
                        }
                    ]
                }
            },
            {
                "bool": {
                    "must": [
                        {
                            "term": {
                                "entityType.keyword": "FOLDER"
                            }
                        },
                        {
                            "term": {
                                "systemAttributes.parentId.keyword": "root"
                            }
                        }
                    ]
                }
            }
        ]
    }
}
```

### Query to search for documents that have a specific system attribute.

```json
{
    "bool": {
        "must": [
            {
                "term": {
                    "entityType.keyword": "DOCUMENT"
                }
            },
            {
                "term": {
                    "systemAttributes.id.keyword": "trigger-elastic-index"
                }
            }
        ]
    }
}
```

### Query to search for documents that are not PCI and have a specific document type.

```json
{
    "bool": {
        "should": [
            {
                "bool": {
                    "must": [
                        {
                            "term": {
                                "entityType.keyword": "DOCUMENT"
                            }
                        },
                        {
                            "term": {
                                "authorization.isPci": false
                            }
                        },
                        {
                            "terms": {
                                "commonAttributes.documentType.keyword": [
                                    "payroll::RecruitingAndHiring",
                                    "payroll::MedicalAndHealth",
                                    "payroll::Benefits",
                                    "payroll::Personnel",
                                    "payroll::Payroll",
                                    "payroll::PayrollOther",
                                    "payroll::FormI9"
                                ]
                            }
                        },
                        {
                            "nested": {
                                "path": "commonAttributes.offeringAttributes",
                                "query": {
                                    "bool": {
                                        "must": [
                                            {
                                                "term": {
                                                    "commonAttributes.offeringAttributes.offeringId.keyword": "Intuit.workermgmt.employeemgmt"
                                                }
                                            }
                                        ]
                                    }
                                }
                            }
                        },
                        {
                            "term": {
                                "systemAttributes.parentId.keyword": "4afb876d-2de7-4cf2-a36f-269fd055c97d"
                            }
                        }
                    ]
                }
            },
            {
                "bool": {
                    "must": [
                        {
                            "term": {
                                "entityType.keyword": "FOLDER"
                            }
                        },
                        {
                            "term": {
                                "authorization.isPci": false
                            }
                        },
                        {
                            "term": {
                                "systemAttributes.parentId.keyword": "4afb876d-2de7-4cf2-a36f-269fd055c97d"
                            }
                        }
                    ]
                }
            }
        ]
    }
}
```

### Query to search for documents that are not PCI and have a specific application attributes.

```json
{
    "bool": {
        "must": [
            {
                "term": {
                    "entityType.keyword": "FOLDER"
                }
            },
            {
                "term": {
                    "commonAttributes.applicationAttributes.relationshipId.keyword": "9130357527468836"
                }
            },
            {
                "term": {
                    "commonAttributes.applicationAttributes.relationshipType.keyword": "realm"
                }
            },
            {
                "term": {
                    "commonAttributes.applicationAttributes.category.keyword": "_shared.collab"
                }
            },
            {
                "term": {
                    "authorization.isPci": false
                }
            },
            {
                "term": {
                    "commonAttributes.applicationAttributes.subcategory.keyword": "iep.qblive"
                }
            }
        ]
    }
}
```

### Query to search for documents that are not PCI and have a specific offering ID and external association.

```json
{
    "bool": {
        "should": [
            {
                "bool": {
                    "must": [
                        {
                            "term": {
                                "entityType.keyword": "DOCUMENT"
                            }
                        },
                        {
                            "term": {
                                "authorization.isPci": false
                            }
                        },
                        {
                            "nested": {
                                "path": "commonAttributes.offeringAttributes",
                                "query": {
                                    "bool": {
                                        "must": [
                                            {
                                                "term": {
                                                    "commonAttributes.offeringAttributes.offeringId.keyword": "Intuit.intcollabs.collab.collabvep"
                                                }
                                            },
                                            {
                                                "prefix": {
                                                    "commonAttributes.offeringAttributes.externalAssociations.keyword": "vep://reqId/557ab504-b291-42f6-9f07-7bd159cdce5d"
                                                }
                                            }
                                        ]
                                    }
                                }
                            }
                        }
                    ]
                }
            }
        ]
    }
}
```