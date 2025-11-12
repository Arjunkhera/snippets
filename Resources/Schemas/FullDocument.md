### Request

```json
{
    "query": {
        "bool": {
            "must": [
                {
                    "term": {
                        "systemAttributes.id.keyword" : "05fcb2b4-d79a-4325-9d37-f24df76fc84f"
                    }
                }
            ]
        }
    }
}
```

### Response

```json
{
    "took": 4,
    "timed_out": false,
    "_shards": {
        "total": 4,
        "successful": 4,
        "skipped": 0,
        "failed": 0
    },
    "hits": {
        "total": {
            "value": 1,
            "relation": "eq"
        },
        "max_score": 28.026207,
        "hits": [
            {
                "_index": "entities-v4",
                "_id": "4621027474543685332_05fcb2b4-d79a-4325-9d37-f24df76fc84f",
                "_score": 28.026207,
                "_routing": "4621027474543685332",
                "_type": "_doc",
                "_source": {
                    "entityType": "DOCUMENT",
                    "authorization": {
                        "ownershipType": "OWNED",
                        "authType": "REALM",
                        "authId": "4621027474543685332",
                        "sharedByAuth": {
                            "authId": "4621027474543685332",
                            "authType": "REALM"
                        },
                        "sharedToAuth": [
                            {
                                "authId": "4621027474543685332",
                                "authType": "REALM"
                            }
                        ],
                        "ownerMetadata": {
                            "accountId": "4621027474543685332",
                            "accountType": "realm",
                            "contextId": "4621027474543685332",
                            "contextType": "realm",
                            "ownershipType": "realm"
                        },
                        "permissionPrecedence": 0,
                        "routingId": "4621027474543685332",
                        "accessType": "OWNED",
                        "isPci": false,
                        "isAuthZ": false,
                        "isTargetState": false
                    },
                    "organizationAttributes": {
                        "folderPath": "root",
                        "parentFolderId": "root",
                        "folderPathIds": [
                            "root"
                        ]
                    },
                    "systemAttributes": {
                        "id": "05fcb2b4-d79a-4325-9d37-f24df76fc84f",
                        "version": "1762952418708|document|05fcb2b4-d79a-4325-9d37-f24df76fc84f",
                        "userCreateDate": 1762952413037,
                        "createDate": 1762952418708,
                        "modifyDate": 1762952418642,
                        "ttlExpDate": 1763038813036,
                        "owner": {
                            "namespaceId": "4621027474543685332",
                            "realmId": "4621027474543685332",
                            "ownerAccountId": "4621027474543685332",
                            "ownerAccountType": "REALM"
                        },
                        "ownerMetadata": {
                            "accountId": "4621027474543685332",
                            "accountType": "realm",
                            "contextId": "4621027474543685332",
                            "contextType": "realm",
                            "ownershipType": "realm"
                        },
                        "creatorMetadata": {
                            "creatorUserId": "4621097880539426397",
                            "creatorAccountId": "4621027474543685332",
                            "creatorPersonaId": "9341456116297449",
                            "creatorUserIdPseudonym": "133e281b0e8967f4d11adc73e568db33de6",
                            "creatorRealmId": "4621027474543685332",
                            "creatorNamespaceId": "50000003"
                        },
                        "assetId": "4324599134368577128",
                        "lastUpdatingAssetId": "4324599134368577128",
                        "semanticSource": "SYSTEM_GENERATED",
                        "dataExtractionStatus": "ASYNC_COMPLETED",
                        "extractor": "dup",
                        "extractionConfidence": 1.0,
                        "offeringId": "Intuit.app.uicomponents.taxformsuploadwidget",
                        "semanticHash": "287d1d4d8a9df79fc33743210af78ce6",
                        "createdBy": "4621097880539426397",
                        "modifiedBy": "4621097880539426397",
                        "appCreated": "Intuit.platform.fdp.docservice",
                        "appModified": "Intuit.platform.fdp.docservice",
                        "originalDocumentName": "Test-1.png",
                        "masterVersion": 1762952418643,
                        "isTargetState": false,
                        "isAutoEnforcedTTL": false,
                        "selfLocator": "/documents/05fcb2b4-d79a-4325-9d37-f24df76fc84f",
                        "channel": "upload",
                        "sourceLocators": [
                            {
                                "contentType": "image/png",
                                "index": "1",
                                "locator": "/documents/05fcb2b4-d79a-4325-9d37-f24df76fc84f/sources/1",
                                "thumbnailPresent": true,
                                "size": 326603,
                                "virusScanStatus": "CLEAN",
                                "contentModerationStatus": "PENDING",
                                "largeFile": false,
                                "thumbnailLocators": [
                                    {
                                        "thumbnailType": "medium",
                                        "locator": "/documents/05fcb2b4-d79a-4325-9d37-f24df76fc84f/sources/1/thumbnails?imageSize=medium",
                                        "contentType": "image/jpeg"
                                    },
                                    {
                                        "thumbnailType": "large",
                                        "locator": "/documents/05fcb2b4-d79a-4325-9d37-f24df76fc84f/sources/1/thumbnails?imageSize=large",
                                        "contentType": "image/jpeg"
                                    },
                                    {
                                        "thumbnailType": "extraLarge",
                                        "locator": "/documents/05fcb2b4-d79a-4325-9d37-f24df76fc84f/sources/1/thumbnails?imageSize=extraLarge",
                                        "contentType": "image/jpeg"
                                    }
                                ]
                            }
                        ],
                        "alternateDataLocators": [
                            {
                                "contentType": "rawSemanticData",
                                "alternateDataType": "rawSemanticData",
                                "locator": "/documents/05fcb2b4-d79a-4325-9d37-f24df76fc84f/alternateData/rawSemanticData"
                            },
                            {
                                "contentType": "desResponseData",
                                "alternateDataType": "desResponseData",
                                "locator": "/documents/05fcb2b4-d79a-4325-9d37-f24df76fc84f/alternateData/desResponseData"
                            },
                            {
                                "contentType": "desRequestData",
                                "alternateDataType": "desRequestData",
                                "locator": "/documents/05fcb2b4-d79a-4325-9d37-f24df76fc84f/alternateData/desRequestData"
                            }
                        ],
                        "size": 326603,
                        "parentId": "root"
                    },
                    "commonAttributes": {
                        "name": "Test-1.png",
                        "documentType": "W2",
                        "ttlDuration": "1d",
                        "location": {
                            "lat": "0",
                            "lng": "0",
                            "address": {
                                "addressLine1": "123 Main St",
                                "addressLine2": "Apt 1",
                                "addressLine3": "Apt 2",
                                "country": "US",
                                "state": "CA",
                                "city": "Mountain View",
                                "zip": "94043"
                            }
                        },
                        "is7216": false,
                        "semanticVersion": "2.0.0",
                        "annotation": "Annotation",
                        "providerName": "Intuit",
                        "taxYear": "2023",
                        "companyRealmId": "123456789",
                        "providerId": "123",
                        "credentialSetId": "123456789",
                        "userConsentRequired": false,
                        "description": "Description",
                        "notes": "Notes",
                        "applicationAttributes": {
                            "relationshipId": "123456789",
                            "relationshipType": "employee",
                            "category": "payroll",
                            "accountNumber": "123456789",
                            "statementDate": 1697198753451,
                            "dueDate": 1697198753451,
                            "subcategory": "payroll",
                            "relationshipList": [
                                {
                                    "relationshipId": "123456789",
                                    "relationshipType": "employee",
                                    "category": "payroll",
                                    "subcategory": "payroll"
                                }
                            ]
                        },
                        "notificationAttributes": {
                            "destination": {
                                "type": "email",
                                "value": "value",
                                "alias": "value"
                            }
                        },
                        "complianceAttributes": {
                            "forbidUpdate": false,
                            "forbidDelete": false,
                            "restrictUpdate": false,
                            "includeInDG": [
                                "DELETE",
                                "ACCESS"
                            ]
                        },
                        "additionalIds": {
                            "correlationId": "33f5a2a8-1492-4dec-8bb9-a6dac5796af2"
                        },
                        "domainAttributes": [
                            {
                                "domain": "BUSINESS",
                                "nameValues": [
                                    {
                                        "name": "documentStatus",
                                        "value": "System generated"
                                    },
                                    {
                                        "name": "region",
                                        "value": "us"
                                    }
                                ]
                            }
                        ],
                        "offeringAttributes": [
                            {
                                "offeringId": "Intuit.workermgmt.employeemgmt",
                                "externalAssociations": [
                                    "123"
                                ],
                                "nameValues": [
                                    {
                                        "name": "documentStatus",
                                        "value": "System generated"
                                    },
                                    {
                                        "name": "region",
                                        "value": "us"
                                    }
                                ]
                            }
                        ],
                        "tags": [
                            "tag-1"
                        ]
                    },
                    "semanticData": {
                        "fdpW2V2": {
                            "taxYear": "2014",
                            "employeeSSN": "123-45-6789",
                            "employerEIN": "11-2233445",
                            "employerName": {
                                "businessNameLine1": "The Big Company"
                            },
                            "employerUSAddress": {
                                "addressLine1Txt": "123 Main Street",
                                "cityNm": "Anywhere",
                                "stateAbbreviationCd": "PA",
                                "zipcd": "12345"
                            },
                            "controlNum": "A1B2",
                            "employeeNm": {
                                "personNameDetail": {
                                    "personFullName": "Jane A DOE",
                                    "personFirstName": "Jane",
                                    "personMiddleName": "A",
                                    "personLastName": "DOE"
                                }
                            },
                            "employeeUSAddress": {
                                "addressLine1Txt": "123 Elm Street",
                                "cityNm": "Anywhere",
                                "stateAbbreviationCd": "PA",
                                "zipcd": "23456"
                            },
                            "wagesAmt": "48500.0",
                            "withholdingAmt": "6835.0",
                            "socialSecurityWagesAmt": "50000.0",
                            "socialSecurityTaxAmt": "3100.0",
                            "medicareWagesAndTipsAmt": "50000.0",
                            "medicareTaxWithheldAmt": "725.0",
                            "employersUseGrps": [
                                {
                                    "employersUseCd": "D"
                                },
                                {
                                    "employersUseCd": "DD"
                                },
                                {
                                    "employersUseCd": "P"
                                }
                            ],
                            "retirementPlanInd": "X",
                            "w2StateLocalTaxGrps": [
                                {
                                    "w2StateTaxGrp": {
                                        "stateAbbreviationCd": "PA",
                                        "employerStateIdNum": "1235",
                                        "stateWagesAmt": "50000.0",
                                        "stateIncomeTaxAmt": "1535.0"
                                    }
                                },
                                {
                                    "w2StateTaxGrp": {
                                        "w2LocalTaxGrp": {
                                            "localWagesAndTipsAmt": "50000.0",
                                            "localIncomeTaxAmt": "750.0",
                                            "localityNm": "MU"
                                        }
                                    }
                                }
                            ],
                            "metadata": {
                                "taxYear": {
                                    "rawValue": "2014",
                                    "confidence": "0.8765000000000001",
                                    "location": {
                                        "bottom": "0.561568945646286",
                                        "left": "0.8330218195915222",
                                        "right": "0.8856727965176105",
                                        "top": "0.45342716574668884"
                                    },
                                    "page": "1"
                                },
                                "employeeSSN": {
                                    "rawValue": "123-45-6789",
                                    "confidence": "0.99",
                                    "location": {
                                        "bottom": "0.7237229645252228",
                                        "left": "0.06036286801099777",
                                        "right": "0.08577940985560417",
                                        "top": "0.6042284369468689"
                                    },
                                    "page": "1"
                                },
                                "employerEIN": {
                                    "rawValue": "11-2233445",
                                    "confidence": "0.885",
                                    "location": {
                                        "bottom": "0.6892558932304382",
                                        "left": "0.11765272915363312",
                                        "right": "0.14330031350255013",
                                        "top": "0.5789044499397278"
                                    },
                                    "page": "1"
                                },
                                "employerName": {
                                    "businessNameLine1Txt": {
                                        "rawValue": "The Big Company",
                                        "confidence": "0.9415396451950073",
                                        "location": {
                                            "bottom": "0.8769141137599945",
                                            "left": "0.2136419415473938",
                                            "right": "0.31776829808950424",
                                            "top": "0.6813818216323853"
                                        },
                                        "page": "1"
                                    }
                                },
                                "employerUSAddress": {
                                    "addressLine1Txt": {
                                        "rawValue": "123 Main Street",
                                        "confidence": "0.94",
                                        "location": {
                                            "bottom": "0.8769141137599945",
                                            "left": "0.2136419415473938",
                                            "right": "0.31776829808950424",
                                            "top": "0.6813818216323853"
                                        },
                                        "page": "1"
                                    },
                                    "cityNm": {
                                        "rawValue": "Anywhere",
                                        "confidence": "0.959563492063492",
                                        "location": {
                                            "bottom": "0.8769141137599945",
                                            "left": "0.2136419415473938",
                                            "right": "0.31776829808950424",
                                            "top": "0.6813818216323853"
                                        },
                                        "page": "1"
                                    },
                                    "stateAbbreviationCd": {
                                        "rawValue": "PA",
                                        "confidence": "0.9868158694041825",
                                        "location": {
                                            "bottom": "0.8769141137599945",
                                            "left": "0.2136419415473938",
                                            "right": "0.31776829808950424",
                                            "top": "0.6813818216323853"
                                        },
                                        "page": "1"
                                    },
                                    "zipcd": {
                                        "rawValue": "12345",
                                        "confidence": "0.9816666666666667",
                                        "location": {
                                            "bottom": "0.8769141137599945",
                                            "left": "0.2136419415473938",
                                            "right": "0.31776829808950424",
                                            "top": "0.6813818216323853"
                                        },
                                        "page": "1"
                                    }
                                },
                                "controlNum": {
                                    "rawValue": "A1B2",
                                    "confidence": "0.7",
                                    "location": {
                                        "bottom": "0.8087457828223705",
                                        "left": "0.36542245745658875",
                                        "right": "0.3917684890329838",
                                        "top": "0.7562277317047119"
                                    },
                                    "page": "1"
                                },
                                "employeeNm": {
                                    "personNameDetail": {
                                        "personFullName": {
                                            "rawValue": "Jane A DOE",
                                            "confidence": "0.6010148525238037",
                                            "location": {
                                                "bottom": "0.8762313425540924",
                                                "left": "0.4568386375904083",
                                                "right": "0.48251704312860966",
                                                "top": "0.7311086058616638"
                                            },
                                            "page": "1"
                                        },
                                        "personFirstName": {
                                            "rawValue": "Jane",
                                            "confidence": "0.9034260511398315",
                                            "location": {
                                                "bottom": "0.8762313425540924",
                                                "left": "0.4568386375904083",
                                                "right": "0.48251704312860966",
                                                "top": "0.7311086058616638"
                                            },
                                            "page": "1"
                                        },
                                        "personMiddleName": {
                                            "rawValue": "A",
                                            "confidence": "0.7399879097938538",
                                            "location": {
                                                "bottom": "0.8762313425540924",
                                                "left": "0.4568386375904083",
                                                "right": "0.48251704312860966",
                                                "top": "0.7311086058616638"
                                            },
                                            "page": "1"
                                        },
                                        "personLastName": {
                                            "rawValue": "DOE",
                                            "confidence": "0.8676008582115173",
                                            "location": {
                                                "bottom": "0.8762313425540924",
                                                "left": "0.4568386375904083",
                                                "right": "0.48251704312860966",
                                                "top": "0.7311086058616638"
                                            },
                                            "page": "1"
                                        }
                                    }
                                },
                                "employeeUSAddress": {
                                    "addressLine1Txt": {
                                        "rawValue": "123 Elm Street",
                                        "confidence": "0.735",
                                        "location": {
                                            "bottom": "0.8778691589832306",
                                            "left": "0.48583564162254333",
                                            "right": "0.5627170130610466",
                                            "top": "0.6294415593147278"
                                        },
                                        "page": "1"
                                    },
                                    "cityNm": {
                                        "rawValue": "Anywhere",
                                        "confidence": "0.8302857142857144",
                                        "location": {
                                            "bottom": "0.8778691589832306",
                                            "left": "0.48583564162254333",
                                            "right": "0.5627170130610466",
                                            "top": "0.6294415593147278"
                                        },
                                        "page": "1"
                                    },
                                    "stateAbbreviationCd": {
                                        "rawValue": "PA",
                                        "confidence": "0.9729270882063998",
                                        "location": {
                                            "bottom": "0.8778691589832306",
                                            "left": "0.48583564162254333",
                                            "right": "0.5627170130610466",
                                            "top": "0.6294415593147278"
                                        },
                                        "page": "1"
                                    },
                                    "zipcd": {
                                        "rawValue": "23456",
                                        "confidence": "0.96",
                                        "location": {
                                            "bottom": "0.8778691589832306",
                                            "left": "0.48583564162254333",
                                            "right": "0.5627170130610466",
                                            "top": "0.6294415593147278"
                                        },
                                        "page": "1"
                                    }
                                },
                                "wagesAmt": {
                                    "rawValue": "48500.0",
                                    "confidence": "0.9610243902439024",
                                    "location": {
                                        "bottom": "0.3759606257081032",
                                        "left": "0.12295541912317276",
                                        "right": "0.15302077122032642",
                                        "top": "0.28191736340522766"
                                    },
                                    "page": "1"
                                },
                                "withholdingAmt": {
                                    "rawValue": "6835.0",
                                    "confidence": "0.8971161396434635",
                                    "location": {
                                        "bottom": "0.16910719871520996",
                                        "left": "0.12334828078746796",
                                        "right": "0.15340577438473701",
                                        "top": "0.08747345954179764"
                                    },
                                    "page": "1"
                                },
                                "socialSecurityWagesAmt": {
                                    "rawValue": "50000.0",
                                    "confidence": "0.9542587929759033",
                                    "location": {
                                        "bottom": "0.3748689293861389",
                                        "left": "0.18547894060611725",
                                        "right": "0.21534093469381332",
                                        "top": "0.281551331281662"
                                    },
                                    "page": "1"
                                },
                                "socialSecurityTaxAmt": {
                                    "rawValue": "3100.0",
                                    "confidence": "0.915474996153966",
                                    "location": {
                                        "bottom": "0.16408252716064453",
                                        "left": "0.18549807369709015",
                                        "right": "0.21610416285693645",
                                        "top": "0.08175283670425415"
                                    },
                                    "page": "1"
                                },
                                "medicareWagesAndTipsAmt": {
                                    "rawValue": "50000.0",
                                    "confidence": "0.9437525497271081",
                                    "location": {
                                        "bottom": "0.3754102811217308",
                                        "left": "0.2509351968765259",
                                        "right": "0.2809667829424143",
                                        "top": "0.28151246905326843"
                                    },
                                    "page": "1"
                                },
                                "medicareTaxWithheldAmt": {
                                    "rawValue": "725.0",
                                    "confidence": "0.932027027027027",
                                    "location": {
                                        "bottom": "0.16366706788539886",
                                        "left": "0.2504729926586151",
                                        "right": "0.27710919454693794",
                                        "top": "0.0997345820069313"
                                    },
                                    "page": "1"
                                },
                                "employersUseGrps": [
                                    {
                                        "employersUseCd": {
                                            "rawValue": "D",
                                            "confidence": "0.998700180053711",
                                            "location": {
                                                "bottom": "0.2028625588864088",
                                                "left": "0.4412170648574829",
                                                "right": "0.4656422361731529",
                                                "top": "0.18858397006988525"
                                            },
                                            "page": "1"
                                        }
                                    },
                                    {
                                        "employersUseCd": {
                                            "rawValue": "DD",
                                            "confidence": "0.9993239593505859",
                                            "location": {
                                                "bottom": "0.21153968758881092",
                                                "left": "0.5042515993118286",
                                                "right": "0.5305638443678617",
                                                "top": "0.18222805857658386"
                                            },
                                            "page": "1"
                                        }
                                    },
                                    {
                                        "employersUseCd": {
                                            "rawValue": "P",
                                            "confidence": "0.9922780609130859",
                                            "location": {
                                                "bottom": "0.20444266311824322",
                                                "left": "0.5652762651443481",
                                                "right": "0.592409148812294",
                                                "top": "0.19131259620189667"
                                            },
                                            "page": "1"
                                        }
                                    }
                                ],
                                "retirementPlanInd": {
                                    "rawValue": "X",
                                    "confidence": "0.9998072814941407",
                                    "location": {
                                        "bottom": "0.3583973217755556",
                                        "left": "0.5050095915794373",
                                        "right": "0.5348623972386122",
                                        "top": "0.3393007814884186"
                                    },
                                    "page": "1"
                                },
                                "w2StateLocalTaxGrps": [
                                    {
                                        "w2StateTaxGrp": {
                                            "stateAbbreviationCd": {
                                                "rawValue": "PA",
                                                "confidence": "0.9986192321777344",
                                                "location": {
                                                    "bottom": "0.9703891687095165",
                                                    "left": "0.7225179076194763",
                                                    "right": "0.8164018094539642",
                                                    "top": "0.9218955039978027"
                                                },
                                                "page": "1"
                                            },
                                            "employerStateIdNum": {
                                                "rawValue": "1235",
                                                "confidence": "0.4832692307692308",
                                                "location": {
                                                    "bottom": "0.9148510098457336",
                                                    "left": "0.7253302931785583",
                                                    "right": "0.8154211714863777",
                                                    "top": "0.6947396993637085"
                                                },
                                                "page": "1"
                                            },
                                            "stateWagesAmt": {
                                                "rawValue": "50000.0",
                                                "confidence": "0.947525230998025",
                                                "location": {
                                                    "bottom": "0.6886148750782013",
                                                    "left": "0.7249005436897278",
                                                    "right": "0.816730409860611",
                                                    "top": "0.5427360534667969"
                                                },
                                                "page": "1"
                                            },
                                            "stateIncomeTaxAmt": {
                                                "rawValue": "1535.0",
                                                "confidence": "0.8802808769171323",
                                                "location": {
                                                    "bottom": "0.5377173274755478",
                                                    "left": "0.7241249084472656",
                                                    "right": "0.8170453980565071",
                                                    "top": "0.4033606946468353"
                                                },
                                                "page": "1"
                                            }
                                        }
                                    },
                                    {
                                        "w2StateTaxGrp": {
                                            "w2LocalTaxGrp": {
                                                "localWagesAndTipsAmt": {
                                                    "rawValue": "50000.0",
                                                    "confidence": "0.9512726952267393",
                                                    "location": {
                                                        "bottom": "0.39804719388484955",
                                                        "left": "0.7243371605873108",
                                                        "right": "0.817475825548172",
                                                        "top": "0.2500306963920593"
                                                    },
                                                    "page": "1"
                                                },
                                                "localIncomeTaxAmt": {
                                                    "rawValue": "750.0",
                                                    "confidence": "0.874",
                                                    "location": {
                                                        "bottom": "0.24517211318016052",
                                                        "left": "0.7244519591331482",
                                                        "right": "0.8143139481544495",
                                                        "top": "0.11165045201778412"
                                                    },
                                                    "page": "1"
                                                },
                                                "localityNm": {
                                                    "rawValue": "MU",
                                                    "confidence": "0.7132619047619047",
                                                    "location": {
                                                        "bottom": "0.10665949434041977",
                                                        "left": "0.7213311195373535",
                                                        "right": "0.8182342201471329",
                                                        "top": "0.021097473800182343"
                                                    },
                                                    "page": "1"
                                                }
                                            }
                                        }
                                    }
                                ]
                            }
                        }
                    }
                }
            }
        ]
    }
}
```