"""
Elasticsearch Query Generator Tool

This tool generates syntactically valid Elasticsearch DSL queries for the entities-v4 index
based on natural language descriptions using Claude Sonnet 4.5.

Dependencies:
    - anthropic >= 0.18.0
    - elasticsearch-dsl >= 8.0.0

Environment Variables:
    - ANTHROPIC_API_KEY: Valid Anthropic API key (required)
"""

import os
import json
import time
from typing import Dict, Any

# Requires: anthropic >= 0.18.0
try:
    from anthropic import Anthropic, APIError, AuthenticationError, APIConnectionError
except ImportError:
    Anthropic = None
    APIError = None
    AuthenticationError = None
    APIConnectionError = None

# Requires: elasticsearch-dsl >= 8.0.0
try:
    from elasticsearch_dsl import Q, Search
    from elasticsearch_dsl.exceptions import ValidationException
except ImportError:
    Q = None
    Search = None
    ValidationException = None


# --- Embedded Resources ---

# Complete Elasticsearch mapping for entities-v4 index
ELASTICSEARCH_MAPPING = """
{
    "entities-v4" : {
      "mappings" : {
        "dynamic" : "false",
        "properties" : {
          "authorization" : {
            "properties" : {
              "accessType" : {
                "type" : "text",
                "fields" : {
                  "keyword" : {
                    "type" : "keyword",
                    "ignore_above" : 256
                  }
                }
              },
              "authId" : {
                "type" : "text",
                "fields" : {
                  "keyword" : {
                    "type" : "keyword",
                    "ignore_above" : 256
                  }
                }
              },
              "authType" : {
                "type" : "text",
                "fields" : {
                  "keyword" : {
                    "type" : "keyword",
                    "ignore_above" : 256
                  }
                }
              },
              "isAuthZ" : {
                "type" : "boolean"
              },
              "isPci" : {
                "type" : "boolean"
              },
              "isTargetState" : {
                "type" : "boolean"
              },
              "ownerMetadata" : {
                "properties" : {
                  "accountId" : {
                    "type" : "text",
                    "fields" : {
                      "keyword" : {
                        "type" : "keyword",
                        "ignore_above" : 256
                      }
                    }
                  },
                  "contextId" : {
                    "type" : "text",
                    "fields" : {
                      "keyword" : {
                        "type" : "keyword",
                        "ignore_above" : 256
                      }
                    }
                  },
                  "contextType" : {
                    "type" : "text",
                    "fields" : {
                      "keyword" : {
                        "type" : "keyword",
                        "ignore_above" : 256
                      }
                    }
                  },
                  "identifier" : {
                    "type" : "text",
                    "fields" : {
                      "keyword" : {
                        "type" : "keyword",
                        "ignore_above" : 256
                      }
                    }
                  },
                  "identifierType" : {
                    "type" : "text",
                    "fields" : {
                      "keyword" : {
                        "type" : "keyword",
                        "ignore_above" : 256
                      }
                    }
                  },
                  "ownershipType" : {
                    "type" : "text",
                    "fields" : {
                      "keyword" : {
                        "type" : "keyword",
                        "ignore_above" : 256
                      }
                    }
                  }
                }
              },
              "ownershipType" : {
                "type" : "text",
                "fields" : {
                  "keyword" : {
                    "type" : "keyword",
                    "ignore_above" : 256
                  }
                }
              },
              "permissionPrecedence" : {
                "type" : "integer",
                "fields" : {
                  "keyword" : {
                    "type" : "keyword",
                    "ignore_above" : 256
                  }
                }
              },
              "precedenceValue" : {
                "type" : "integer",
                "fields" : {
                  "keyword" : {
                    "type" : "keyword",
                    "ignore_above" : 256
                  }
                }
              },
              "sharedByAuth" : {
                "properties" : {
                  "authId" : {
                    "type" : "text",
                    "fields" : {
                      "keyword" : {
                        "type" : "keyword",
                        "ignore_above" : 256
                      }
                    }
                  },
                  "authType" : {
                    "type" : "text",
                    "fields" : {
                      "keyword" : {
                        "type" : "keyword",
                        "ignore_above" : 256
                      }
                    }
                  }
                }
              },
              "sharedToAuth" : {
                "type" : "nested",
                "properties" : {
                  "authId" : {
                    "type" : "text",
                    "fields" : {
                      "keyword" : {
                        "type" : "keyword",
                        "ignore_above" : 256
                      }
                    }
                  },
                  "authType" : {
                    "type" : "text",
                    "fields" : {
                      "keyword" : {
                        "type" : "keyword",
                        "ignore_above" : 256
                      }
                    }
                  }
                }
              },
              "sharingAttributes" : {
                "properties" : {
                  "sharedBy" : {
                    "properties" : {
                      "accountId" : {
                        "type" : "text",
                        "fields" : {
                          "keyword" : {
                            "type" : "keyword",
                            "ignore_above" : 256
                          }
                        }
                      },
                      "contextId" : {
                        "type" : "text",
                        "fields" : {
                          "keyword" : {
                            "type" : "keyword",
                            "ignore_above" : 256
                          }
                        }
                      },
                      "contextType" : {
                        "type" : "text",
                        "fields" : {
                          "keyword" : {
                            "type" : "keyword",
                            "ignore_above" : 256
                          }
                        }
                      },
                      "identifier" : {
                        "type" : "text",
                        "fields" : {
                          "keyword" : {
                            "type" : "keyword",
                            "ignore_above" : 256
                          }
                        }
                      },
                      "identifierType" : {
                        "type" : "text",
                        "fields" : {
                          "keyword" : {
                            "type" : "keyword",
                            "ignore_above" : 256
                          }
                        }
                      }
                    }
                  },
                  "sharedTo" : {
                    "properties" : {
                      "accountId" : {
                        "type" : "text",
                        "fields" : {
                          "keyword" : {
                            "type" : "keyword",
                            "ignore_above" : 256
                          }
                        }
                      },
                      "identifier" : {
                        "type" : "text",
                        "fields" : {
                          "keyword" : {
                            "type" : "keyword",
                            "ignore_above" : 256
                          }
                        }
                      },
                      "identifierType" : {
                        "type" : "text",
                        "fields" : {
                          "keyword" : {
                            "type" : "keyword",
                            "ignore_above" : 256
                          }
                        }
                      }
                    }
                  }
                }
              }
            }
          },
          "commonAttributes" : {
            "properties" : {
              "additionalIds" : {
                "properties" : {
                  "attachmentId" : {
                    "type" : "text",
                    "fields" : {
                      "keyword" : {
                        "type" : "keyword",
                        "ignore_above" : 256
                      }
                    }
                  },
                  "correlationId" : {
                    "type" : "text",
                    "fields" : {
                      "keyword" : {
                        "type" : "keyword",
                        "ignore_above" : 256
                      }
                    }
                  },
                  "linkedSourceDocIds" : {
                    "type" : "text",
                    "fields" : {
                      "keyword" : {
                        "type" : "keyword",
                        "ignore_above" : 256
                      }
                    }
                  },
                  "requestCorrelationId" : {
                    "type" : "text",
                    "fields" : {
                      "keyword" : {
                        "type" : "keyword",
                        "ignore_above" : 256
                      }
                    }
                  },
                  "secondaryId" : {
                    "type" : "text",
                    "fields" : {
                      "keyword" : {
                        "type" : "keyword",
                        "ignore_above" : 256
                      }
                    }
                  }
                }
              },
              "annotation" : {
                "type" : "text",
                "fields" : {
                  "keyword" : {
                    "type" : "keyword",
                    "ignore_above" : 256
                  }
                }
              },
              "applicationAttributes" : {
                "properties" : {
                  "accountNumber" : {
                    "type" : "text",
                    "fields" : {
                      "keyword" : {
                        "type" : "keyword",
                        "ignore_above" : 256
                      }
                    }
                  },
                  "category" : {
                    "type" : "text",
                    "fields" : {
                      "keyword" : {
                        "type" : "keyword",
                        "ignore_above" : 256
                      }
                    }
                  },
                  "dueDate" : {
                    "type" : "date",
                    "format" : "strict_date_optional_time||epoch_millis||yyyy/MM/dd||MM/dd/yyyy"
                  },
                  "relationshipId" : {
                    "type" : "text",
                    "fields" : {
                      "keyword" : {
                        "type" : "keyword",
                        "ignore_above" : 256
                      }
                    }
                  },
                  "relationshipList" : {
                    "type" : "nested",
                    "properties" : {
                      "category" : {
                        "type" : "text",
                        "fields" : {
                          "keyword" : {
                            "type" : "keyword",
                            "ignore_above" : 256
                          }
                        }
                      },
                      "relationshipId" : {
                        "type" : "text",
                        "fields" : {
                          "keyword" : {
                            "type" : "keyword",
                            "ignore_above" : 256
                          }
                        }
                      },
                      "relationshipType" : {
                        "type" : "text",
                        "fields" : {
                          "keyword" : {
                            "type" : "keyword",
                            "ignore_above" : 256
                          }
                        }
                      },
                      "subcategory" : {
                        "type" : "text",
                        "fields" : {
                          "keyword" : {
                            "type" : "keyword",
                            "ignore_above" : 256
                          }
                        }
                      }
                    }
                  },
                  "relationshipType" : {
                    "type" : "text",
                    "fields" : {
                      "keyword" : {
                        "type" : "keyword",
                        "ignore_above" : 256
                      }
                    }
                  },
                  "statementDate" : {
                    "type" : "date",
                    "format" : "strict_date_optional_time||epoch_millis||yyyy/MM/dd||MM/dd/yyyy"
                  },
                  "subcategory" : {
                    "type" : "text",
                    "fields" : {
                      "keyword" : {
                        "type" : "keyword",
                        "ignore_above" : 256
                      }
                    }
                  }
                }
              },
              "archivalJobId" : {
                "type" : "text",
                "fields" : {
                  "keyword" : {
                    "type" : "keyword",
                    "ignore_above" : 256
                  }
                }
              },
              "authorizationAttributes" : {
                "properties" : {
                  "environment" : {
                    "type" : "nested",
                    "properties" : {
                      "name" : {
                        "type" : "text",
                        "fields" : {
                          "keyword" : {
                            "type" : "keyword",
                            "ignore_above" : 256
                          }
                        }
                      },
                      "value" : {
                        "type" : "text",
                        "fields" : {
                          "keyword" : {
                            "type" : "keyword",
                            "ignore_above" : 256
                          }
                        }
                      }
                    }
                  },
                  "resourceAttributes" : {
                    "type" : "nested",
                    "properties" : {
                      "name" : {
                        "type" : "text",
                        "fields" : {
                          "keyword" : {
                            "type" : "keyword",
                            "ignore_above" : 256
                          }
                        }
                      },
                      "value" : {
                        "type" : "text",
                        "fields" : {
                          "keyword" : {
                            "type" : "keyword",
                            "ignore_above" : 256
                          }
                        }
                      }
                    }
                  },
                  "resourceId" : {
                    "type" : "text",
                    "fields" : {
                      "keyword" : {
                        "type" : "keyword",
                        "ignore_above" : 256
                      }
                    }
                  },
                  "selector" : {
                    "properties" : {
                      "selectorAttributes" : {
                        "type" : "nested",
                        "properties" : {
                          "name" : {
                            "type" : "text",
                            "fields" : {
                              "keyword" : {
                                "type" : "keyword",
                                "ignore_above" : 256
                              }
                            }
                          },
                          "value" : {
                            "type" : "text",
                            "fields" : {
                              "keyword" : {
                                "type" : "keyword",
                                "ignore_above" : 256
                              }
                            }
                          }
                        }
                      },
                      "selectorId" : {
                        "type" : "text",
                        "fields" : {
                          "keyword" : {
                            "type" : "keyword",
                            "ignore_above" : 256
                          }
                        }
                      }
                    }
                  }
                }
              },
              "companyRealmId" : {
                "type" : "text",
                "fields" : {
                  "keyword" : {
                    "type" : "keyword",
                    "ignore_above" : 256
                  }
                }
              },
              "complianceAttributes" : {
                "properties" : {
                  "forbidDelete" : {
                    "type" : "boolean"
                  },
                  "forbidUpdate" : {
                    "type" : "boolean"
                  },
                  "includeInDg2" : {
                    "type" : "boolean"
                  },
                  "restrictUpdate" : {
                    "type" : "boolean"
                  }
                }
              },
              "credentialSetId" : {
                "type" : "text",
                "fields" : {
                  "keyword" : {
                    "type" : "keyword",
                    "ignore_above" : 256
                  }
                }
              },
              "description" : {
                "type" : "text",
                "fields" : {
                  "keyword" : {
                    "type" : "keyword",
                    "ignore_above" : 256,
                    "normalizer" : "case_insensitive"
                  }
                },
                "analyzer" : "edge_ngram_analyzer",
                "search_analyzer" : "lowercase_analyzer"
              },
              "documentType" : {
                "type" : "text",
                "fields" : {
                  "keyword" : {
                    "type" : "keyword",
                    "ignore_above" : 256
                  }
                },
                "analyzer" : "ngram_analyzer",
                "search_analyzer" : "lowercase_analyzer"
              },
              "domainAttributes" : {
                "type" : "nested",
                "properties" : {
                  "domain" : {
                    "type" : "text",
                    "fields" : {
                      "keyword" : {
                        "type" : "keyword",
                        "ignore_above" : 256
                      }
                    }
                  },
                  "nameValues" : {
                    "type" : "nested",
                    "properties" : {
                      "name" : {
                        "type" : "text",
                        "fields" : {
                          "keyword" : {
                            "type" : "keyword",
                            "ignore_above" : 256
                          }
                        }
                      },
                      "value" : {
                        "type" : "text",
                        "fields" : {
                          "keyword" : {
                            "type" : "keyword",
                            "ignore_above" : 256
                          }
                        }
                      }
                    }
                  }
                }
              },
              "import" : {
                "properties" : {
                  "sourceImport" : {
                    "type" : "text",
                    "fields" : {
                      "keyword" : {
                        "type" : "keyword",
                        "ignore_above" : 256
                      }
                    }
                  }
                }
              },
              "is7216" : {
                "type" : "boolean"
              },
              "location" : {
                "properties" : {
                  "address" : {
                    "properties" : {
                      "addressLine1" : {
                        "type" : "text",
                        "fields" : {
                          "keyword" : {
                            "type" : "keyword",
                            "ignore_above" : 256
                          }
                        }
                      },
                      "addressLine2" : {
                        "type" : "text",
                        "fields" : {
                          "keyword" : {
                            "type" : "keyword",
                            "ignore_above" : 256
                          }
                        }
                      },
                      "addressLine3" : {
                        "type" : "text",
                        "fields" : {
                          "keyword" : {
                            "type" : "keyword",
                            "ignore_above" : 256
                          }
                        }
                      },
                      "city" : {
                        "type" : "text",
                        "fields" : {
                          "keyword" : {
                            "type" : "keyword",
                            "ignore_above" : 256
                          }
                        }
                      },
                      "country" : {
                        "type" : "text",
                        "fields" : {
                          "keyword" : {
                            "type" : "keyword",
                            "ignore_above" : 256
                          }
                        }
                      },
                      "state" : {
                        "type" : "text",
                        "fields" : {
                          "keyword" : {
                            "type" : "keyword",
                            "ignore_above" : 256
                          }
                        }
                      },
                      "zip" : {
                        "type" : "text",
                        "fields" : {
                          "keyword" : {
                            "type" : "keyword",
                            "ignore_above" : 256
                          }
                        }
                      }
                    }
                  },
                  "lat" : {
                    "type" : "text",
                    "fields" : {
                      "keyword" : {
                        "type" : "keyword",
                        "ignore_above" : 256
                      }
                    }
                  },
                  "lng" : {
                    "type" : "text",
                    "fields" : {
                      "keyword" : {
                        "type" : "keyword",
                        "ignore_above" : 256
                      }
                    }
                  }
                }
              },
              "name" : {
                "type" : "text",
                "fields" : {
                  "keyword" : {
                    "type" : "keyword",
                    "ignore_above" : 256,
                    "normalizer" : "case_insensitive"
                  }
                },
                "analyzer" : "ngram_analyzer",
                "search_analyzer" : "lowercase_analyzer"
              },
              "notes" : {
                "type" : "text",
                "fields" : {
                  "keyword" : {
                    "type" : "keyword",
                    "ignore_above" : 256
                  }
                }
              },
              "notificationAttributes" : {
                "properties" : {
                  "destination" : {
                    "properties" : {
                      "alias" : {
                        "type" : "text",
                        "fields" : {
                          "keyword" : {
                            "type" : "keyword",
                            "ignore_above" : 256
                          }
                        }
                      },
                      "type" : {
                        "type" : "text",
                        "fields" : {
                          "keyword" : {
                            "type" : "keyword",
                            "ignore_above" : 256
                          }
                        }
                      },
                      "value" : {
                        "type" : "text",
                        "fields" : {
                          "keyword" : {
                            "type" : "keyword",
                            "ignore_above" : 256
                          }
                        }
                      }
                    }
                  }
                }
              },
              "offeringAttributes" : {
                "type" : "nested",
                "properties" : {
                  "externalAssociations" : {
                    "type" : "text",
                    "fields" : {
                      "keyword" : {
                        "type" : "keyword",
                        "ignore_above" : 256
                      }
                    }
                  },
                  "nameValues" : {
                    "type" : "nested",
                    "properties" : {
                      "name" : {
                        "type" : "text",
                        "fields" : {
                          "keyword" : {
                            "type" : "keyword",
                            "ignore_above" : 256
                          }
                        }
                      },
                      "value" : {
                        "type" : "text",
                        "fields" : {
                          "keyword" : {
                            "type" : "keyword",
                            "ignore_above" : 256
                          }
                        }
                      }
                    }
                  },
                  "offeringId" : {
                    "type" : "text",
                    "fields" : {
                      "keyword" : {
                        "type" : "keyword",
                        "ignore_above" : 256
                      }
                    }
                  }
                }
              },
              "payloadVersion" : {
                "type" : "text",
                "fields" : {
                  "keyword" : {
                    "type" : "keyword",
                    "ignore_above" : 256
                  }
                }
              },
              "providerId" : {
                "type" : "text",
                "fields" : {
                  "keyword" : {
                    "type" : "keyword",
                    "ignore_above" : 256
                  }
                }
              },
              "providerName" : {
                "type" : "text",
                "fields" : {
                  "keyword" : {
                    "type" : "keyword",
                    "ignore_above" : 256
                  }
                }
              },
              "semanticVersion" : {
                "type" : "text",
                "fields" : {
                  "keyword" : {
                    "type" : "keyword",
                    "ignore_above" : 256
                  }
                }
              },
              "tags" : {
                "type" : "text",
                "fields" : {
                  "keyword" : {
                    "type" : "keyword",
                    "ignore_above" : 256
                  }
                }
              },
              "taxYear" : {
                "type" : "text",
                "fields" : {
                  "keyword" : {
                    "type" : "keyword",
                    "ignore_above" : 256
                  }
                }
              },
              "userConsentRequired" : {
                "type" : "boolean"
              },
              "userReviewStatus" : {
                "type" : "text",
                "fields" : {
                  "keyword" : {
                    "type" : "keyword",
                    "ignore_above" : 256
                  }
                }
              }
            }
          },
          "entityType" : {
            "type" : "text",
            "fields" : {
              "keyword" : {
                "type" : "keyword",
                "ignore_above" : 256
              }
            }
          },
          "organizationAttributes" : {
            "properties" : {
              "folderPath" : {
                "type" : "text",
                "fields" : {
                  "keyword" : {
                    "type" : "keyword",
                    "ignore_above" : 256
                  }
                }
              },
              "folderPathIds" : {
                "type" : "text",
                "fields" : {
                  "keyword" : {
                    "type" : "keyword",
                    "ignore_above" : 256
                  }
                }
              },
              "parentFolderId" : {
                "type" : "text",
                "fields" : {
                  "keyword" : {
                    "type" : "keyword",
                    "ignore_above" : 256
                  }
                }
              }
            }
          },
          "semanticData" : {
            "type" : "object",
            "enabled" : false
          },
          "systemAttributes" : {
            "properties" : {
              "alternateDataLocators" : {
                "type" : "nested",
                "properties" : {
                  "alternateDataType" : {
                    "type" : "text",
                    "fields" : {
                      "keyword" : {
                        "type" : "keyword",
                        "ignore_above" : 256
                      }
                    }
                  },
                  "contentType" : {
                    "type" : "text",
                    "fields" : {
                      "keyword" : {
                        "type" : "keyword",
                        "ignore_above" : 256
                      }
                    }
                  },
                  "locator" : {
                    "type" : "text",
                    "fields" : {
                      "keyword" : {
                        "type" : "keyword",
                        "ignore_above" : 256
                      }
                    }
                  }
                }
              },
              "appCreated" : {
                "type" : "text",
                "fields" : {
                  "keyword" : {
                    "type" : "keyword",
                    "ignore_above" : 256
                  }
                }
              },
              "appModified" : {
                "type" : "text",
                "fields" : {
                  "keyword" : {
                    "type" : "keyword",
                    "ignore_above" : 256
                  }
                }
              },
              "assetId" : {
                "type" : "text",
                "fields" : {
                  "keyword" : {
                    "type" : "keyword",
                    "ignore_above" : 256
                  }
                }
              },
              "channel" : {
                "type" : "text",
                "fields" : {
                  "keyword" : {
                    "type" : "keyword",
                    "ignore_above" : 256
                  }
                }
              },
              "children" : {
                "type" : "object",
                "enabled" : false
              },
              "classificationDetails" : {
                "properties" : {
                  "confidenceLevel" : {
                    "type" : "text",
                    "fields" : {
                      "keyword" : {
                        "type" : "keyword",
                        "ignore_above" : 256
                      }
                    }
                  },
                  "documentType" : {
                    "type" : "text",
                    "fields" : {
                      "keyword" : {
                        "type" : "keyword",
                        "ignore_above" : 256
                      }
                    }
                  }
                }
              },
              "classificationStatus" : {
                "type" : "text",
                "fields" : {
                  "keyword" : {
                    "type" : "keyword",
                    "ignore_above" : 256
                  }
                }
              },
              "contentModerationAttribute" : {
                "properties" : {
                  "minConfidence" : {
                    "type" : "integer"
                  },
                  "modelProviderName" : {
                    "type" : "text",
                    "fields" : {
                      "keyword" : {
                        "type" : "keyword",
                        "ignore_above" : 256
                      }
                    }
                  },
                  "moderatedDate" : {
                    "type" : "date"
                  },
                  "moderatedPages" : {
                    "type" : "integer"
                  },
                  "rejectedPages" : {
                    "type" : "nested",
                    "properties" : {
                      "confidence" : {
                        "type" : "float"
                      },
                      "labels" : {
                        "type" : "text",
                        "fields" : {
                          "keyword" : {
                            "type" : "keyword",
                            "ignore_above" : 256
                          }
                        }
                      },
                      "pageNumber" : {
                        "type" : "integer"
                      }
                    }
                  }
                }
              },
              "contentModerationStatus" : {
                "type" : "text",
                "fields" : {
                  "keyword" : {
                    "type" : "keyword",
                    "ignore_above" : 256
                  }
                }
              },
              "copiedFrom" : {
                "type" : "text",
                "fields" : {
                  "keyword" : {
                    "type" : "keyword",
                    "ignore_above" : 256
                  }
                }
              },
              "createDate" : {
                "type" : "date",
                "format" : "strict_date_optional_time||epoch_millis"
              },
              "createdBy" : {
                "type" : "text",
                "fields" : {
                  "keyword" : {
                    "type" : "keyword",
                    "ignore_above" : 256
                  }
                }
              },
              "creatorMetadata" : {
                "properties" : {
                  "creatorAccountId" : {
                    "type" : "text",
                    "fields" : {
                      "keyword" : {
                        "type" : "keyword",
                        "ignore_above" : 256
                      }
                    }
                  },
                  "creatorNamespaceId" : {
                    "type" : "text",
                    "fields" : {
                      "keyword" : {
                        "type" : "keyword",
                        "ignore_above" : 256
                      }
                    }
                  },
                  "creatorPersonaId" : {
                    "type" : "text",
                    "fields" : {
                      "keyword" : {
                        "type" : "keyword",
                        "ignore_above" : 256
                      }
                    }
                  },
                  "creatorRealmId" : {
                    "type" : "text",
                    "fields" : {
                      "keyword" : {
                        "type" : "keyword",
                        "ignore_above" : 256
                      }
                    }
                  },
                  "creatorUserId" : {
                    "type" : "text",
                    "fields" : {
                      "keyword" : {
                        "type" : "keyword",
                        "ignore_above" : 256
                      }
                    }
                  },
                  "creatorUserIdPseudonym" : {
                    "type" : "text",
                    "fields" : {
                      "keyword" : {
                        "type" : "keyword",
                        "ignore_above" : 256
                      }
                    }
                  }
                }
              },
              "dataExtractionStatus" : {
                "type" : "text",
                "fields" : {
                  "keyword" : {
                    "type" : "keyword",
                    "ignore_above" : 256
                  }
                }
              },
              "entities" : {
                "type" : "nested",
                "properties" : {
                  "dataSource" : {
                    "type" : "text",
                    "fields" : {
                      "keyword" : {
                        "type" : "keyword",
                        "ignore_above" : 256
                      }
                    }
                  },
                  "entityId" : {
                    "type" : "text",
                    "fields" : {
                      "keyword" : {
                        "type" : "keyword",
                        "ignore_above" : 256
                      }
                    }
                  },
                  "entityType" : {
                    "type" : "text",
                    "fields" : {
                      "keyword" : {
                        "type" : "keyword",
                        "ignore_above" : 256
                      }
                    }
                  },
                  "extractionConfidence" : {
                    "type" : "float"
                  },
                  "extractor" : {
                    "type" : "text",
                    "fields" : {
                      "keyword" : {
                        "type" : "keyword",
                        "ignore_above" : 256
                      }
                    }
                  }
                }
              },
              "entitySupported" : {
                "type" : "boolean"
              },
              "extractionConfidence" : {
                "type" : "float"
              },
              "extractor" : {
                "type" : "text",
                "fields" : {
                  "keyword" : {
                    "type" : "keyword",
                    "ignore_above" : 256
                  }
                }
              },
              "genericDocTypes" : {
                "type" : "text",
                "fields" : {
                  "keyword" : {
                    "type" : "keyword",
                    "ignore_above" : 256
                  }
                }
              },
              "id" : {
                "type" : "text",
                "fields" : {
                  "keyword" : {
                    "type" : "keyword",
                    "ignore_above" : 256
                  }
                }
              },
              "isComposite" : {
                "type" : "boolean"
              },
              "isTargetState" : {
                "type" : "boolean"
              },
              "lastUpdatingAssetId" : {
                "type" : "text",
                "fields" : {
                  "keyword" : {
                    "type" : "keyword",
                    "ignore_above" : 256
                  }
                }
              },
              "masterVersion" : {
                "type" : "date",
                "format" : "strict_date_optional_time||epoch_millis"
              },
              "modifiedBy" : {
                "type" : "text",
                "fields" : {
                  "keyword" : {
                    "type" : "keyword",
                    "ignore_above" : 256
                  }
                }
              },
              "modifyDate" : {
                "type" : "date",
                "format" : "strict_date_optional_time||epoch_millis"
              },
              "offeringId" : {
                "type" : "text",
                "fields" : {
                  "keyword" : {
                    "type" : "keyword",
                    "ignore_above" : 256
                  }
                }
              },
              "originalDocumentName" : {
                "type" : "text",
                "fields" : {
                  "keyword" : {
                    "type" : "keyword",
                    "ignore_above" : 256
                  }
                }
              },
              "originatingAssetId" : {
                "type" : "text",
                "fields" : {
                  "keyword" : {
                    "type" : "keyword",
                    "ignore_above" : 256
                  }
                }
              },
              "owner" : {
                "properties" : {
                  "authId" : {
                    "type" : "text",
                    "fields" : {
                      "keyword" : {
                        "type" : "keyword",
                        "ignore_above" : 256
                      }
                    }
                  },
                  "authZOwnerId" : {
                    "type" : "text",
                    "fields" : {
                      "keyword" : {
                        "type" : "keyword",
                        "ignore_above" : 256
                      }
                    }
                  },
                  "namespaceId" : {
                    "type" : "text",
                    "fields" : {
                      "keyword" : {
                        "type" : "keyword",
                        "ignore_above" : 256
                      }
                    }
                  },
                  "ownerAccountId" : {
                    "type" : "text",
                    "fields" : {
                      "keyword" : {
                        "type" : "keyword",
                        "ignore_above" : 256
                      }
                    }
                  },
                  "ownerAccountType" : {
                    "type" : "text",
                    "fields" : {
                      "keyword" : {
                        "type" : "keyword",
                        "ignore_above" : 256
                      }
                    }
                  },
                  "realmId" : {
                    "type" : "text",
                    "fields" : {
                      "keyword" : {
                        "type" : "keyword",
                        "ignore_above" : 256
                      }
                    }
                  }
                }
              },
              "ownerMetadata" : {
                "properties" : {
                  "accountId" : {
                    "type" : "text",
                    "fields" : {
                      "keyword" : {
                        "type" : "keyword",
                        "ignore_above" : 256
                      }
                    }
                  },
                  "accountType" : {
                    "type" : "text",
                    "fields" : {
                      "keyword" : {
                        "type" : "keyword",
                        "ignore_above" : 256
                      }
                    }
                  },
                  "contextId" : {
                    "type" : "text",
                    "fields" : {
                      "keyword" : {
                        "type" : "keyword",
                        "ignore_above" : 256
                      }
                    }
                  },
                  "contextType" : {
                    "type" : "text",
                    "fields" : {
                      "keyword" : {
                        "type" : "keyword",
                        "ignore_above" : 256
                      }
                    }
                  },
                  "identifierId" : {
                    "type" : "text",
                    "fields" : {
                      "keyword" : {
                        "type" : "keyword",
                        "ignore_above" : 256
                      }
                    }
                  },
                  "identifierType" : {
                    "type" : "text",
                    "fields" : {
                      "keyword" : {
                        "type" : "keyword",
                        "ignore_above" : 256
                      }
                    }
                  },
                  "ownershipType" : {
                    "type" : "text",
                    "fields" : {
                      "keyword" : {
                        "type" : "keyword",
                        "ignore_above" : 256
                      }
                    }
                  }
                }
              },
              "parentId" : {
                "type" : "text",
                "fields" : {
                  "keyword" : {
                    "type" : "keyword",
                    "ignore_above" : 256
                  }
                }
              },
              "pdfConversionStatus" : {
                "type" : "text",
                "fields" : {
                  "keyword" : {
                    "type" : "keyword",
                    "ignore_above" : 256
                  }
                }
              },
              "selfLocator" : {
                "type" : "text",
                "fields" : {
                  "keyword" : {
                    "type" : "keyword",
                    "ignore_above" : 256
                  }
                }
              },
              "semanticHash" : {
                "type" : "text",
                "fields" : {
                  "keyword" : {
                    "type" : "keyword",
                    "ignore_above" : 256
                  }
                }
              },
              "semanticSource" : {
                "type" : "text",
                "fields" : {
                  "keyword" : {
                    "type" : "keyword",
                    "ignore_above" : 256
                  }
                }
              },
              "signatureAttributes" : {
                "properties" : {
                  "envelopeId" : {
                    "type" : "text",
                    "fields" : {
                      "keyword" : {
                        "type" : "keyword",
                        "ignore_above" : 256
                      }
                    }
                  }
                }
              },
              "size" : {
                "type" : "long"
              },
              "sourceLocators" : {
                "type" : "nested",
                "properties" : {
                  "contentModerationStatus" : {
                    "type" : "text",
                    "fields" : {
                      "keyword" : {
                        "type" : "keyword",
                        "ignore_above" : 256
                      }
                    }
                  },
                  "contentType" : {
                    "type" : "text",
                    "fields" : {
                      "keyword" : {
                        "type" : "keyword",
                        "ignore_above" : 256
                      }
                    }
                  },
                  "index" : {
                    "type" : "integer"
                  },
                  "largeFile" : {
                    "type" : "boolean"
                  },
                  "locator" : {
                    "type" : "text",
                    "fields" : {
                      "keyword" : {
                        "type" : "keyword",
                        "ignore_above" : 256
                      }
                    }
                  },
                  "size" : {
                    "type" : "long"
                  },
                  "thumbnailLocators" : {
                    "type" : "nested",
                    "properties" : {
                      "contentType" : {
                        "type" : "text",
                        "fields" : {
                          "keyword" : {
                            "type" : "keyword",
                            "ignore_above" : 256
                          }
                        }
                      },
                      "locator" : {
                        "type" : "text",
                        "fields" : {
                          "keyword" : {
                            "type" : "keyword",
                            "ignore_above" : 256
                          }
                        }
                      },
                      "thumbnailType" : {
                        "type" : "text",
                        "fields" : {
                          "keyword" : {
                            "type" : "keyword",
                            "ignore_above" : 256
                          }
                        }
                      }
                    }
                  },
                  "thumbnailPresent" : {
                    "type" : "boolean"
                  },
                  "virusScanStatus" : {
                    "type" : "text",
                    "fields" : {
                      "keyword" : {
                        "type" : "keyword",
                        "ignore_above" : 256
                      }
                    }
                  }
                }
              },
              "userCreateDate" : {
                "type" : "date",
                "format" : "strict_date_optional_time||epoch_millis"
              },
              "version" : {
                "type" : "text",
                "fields" : {
                  "keyword" : {
                    "type" : "keyword",
                    "ignore_above" : 256
                  }
                }
              }
            }
          },
          "usageType" : {
            "type" : "text",
            "fields" : {
              "keyword" : {
                "type" : "keyword",
                "ignore_above" : 256
              }
            }
          }
        }
      }
    }
  }
"""

# Field descriptions loaded from Resources/Schemas/FieldDescriptions.json
FIELD_DESCRIPTIONS = {
  "authorization": "Authorization and access control information for the entity",
  "authorization.accessType": "Type of access granted (e.g., OWNED, SHARED)",
  "authorization.authId": "Authorization identifier for the entity",
  "authorization.authType": "Type of authorization (e.g., REALM, USER)",
  "authorization.isAuthZ": "Boolean flag indicating if authorization is enabled",
  "authorization.isPci": "Boolean flag indicating if the entity contains PCI (Payment Card Industry) sensitive data",
  "authorization.isTargetState": "Boolean flag indicating if this is a target state for authorization",
  "authorization.ownerMetadata": "Metadata about the owner of the entity",
  "authorization.ownerMetadata.accountId": "Account ID of the owner",
  "authorization.ownerMetadata.contextId": "Context ID for the ownership",
  "authorization.ownerMetadata.contextType": "Type of ownership context (e.g., realm, user)",
  "authorization.ownerMetadata.identifier": "Unique identifier for the owner",
  "authorization.ownerMetadata.identifierType": "Type of identifier used",
  "authorization.ownerMetadata.ownershipType": "Type of ownership (e.g., owned, shared)",
  "authorization.ownershipType": "Overall ownership type for the entity",
  "authorization.permissionPrecedence": "Numeric precedence value for permission resolution",
  "authorization.precedenceValue": "Alternative precedence value field",
  "authorization.sharedByAuth": "Authorization information for who shared the entity",
  "authorization.sharedByAuth.authId": "Auth ID of the sharer",
  "authorization.sharedByAuth.authType": "Auth type of the sharer",
  "authorization.sharedToAuth": "Array of authorization information for entities shared to (nested field)",
  "authorization.sharedToAuth.authId": "Auth ID of the recipient",
  "authorization.sharedToAuth.authType": "Auth type of the recipient",
  "authorization.sharingAttributes": "Detailed sharing attributes",
  "authorization.sharingAttributes.sharedBy": "Information about who shared the entity",
  "authorization.sharingAttributes.sharedBy.accountId": "Account ID of the sharer",
  "authorization.sharingAttributes.sharedBy.contextId": "Context ID of the sharer",
  "authorization.sharingAttributes.sharedBy.contextType": "Context type of the sharer",
  "authorization.sharingAttributes.sharedBy.identifier": "Identifier of the sharer",
  "authorization.sharingAttributes.sharedBy.identifierType": "Type of identifier for the sharer",
  "authorization.sharingAttributes.sharedTo": "Information about who the entity is shared with",
  "authorization.sharingAttributes.sharedTo.accountId": "Account ID of the recipient",
  "authorization.sharingAttributes.sharedTo.identifier": "Identifier of the recipient",
  "authorization.sharingAttributes.sharedTo.identifierType": "Type of identifier for the recipient",
  "commonAttributes": "Common attributes shared across entities",
  "commonAttributes.additionalIds": "Additional identifiers for the entity",
  "commonAttributes.additionalIds.attachmentId": "Unique identifier for attachments",
  "commonAttributes.additionalIds.correlationId": "Correlation ID for tracking related entities",
  "commonAttributes.additionalIds.linkedSourceDocIds": "IDs of linked source documents",
  "commonAttributes.additionalIds.requestCorrelationId": "Correlation ID for the originating request",
  "commonAttributes.additionalIds.secondaryId": "Secondary identifier for the entity",
  "commonAttributes.annotation": "User-added annotation or note for the entity",
  "commonAttributes.applicationAttributes": "Application-specific attributes",
  "commonAttributes.applicationAttributes.accountNumber": "Account number associated with the entity",
  "commonAttributes.applicationAttributes.category": "Category classification for the entity",
  "commonAttributes.applicationAttributes.dueDate": "Due date timestamp for the entity",
  "commonAttributes.applicationAttributes.relationshipId": "ID representing the relationship (e.g., client ID, employee ID)",
  "commonAttributes.applicationAttributes.relationshipList": "Array of relationships associated with the entity",
  "commonAttributes.applicationAttributes.relationshipList.category": "Category of the relationship",
  "commonAttributes.applicationAttributes.relationshipList.relationshipId": "ID of the relationship",
  "commonAttributes.applicationAttributes.relationshipList.relationshipType": "Type of relationship (e.g., client, employee, vendor)",
  "commonAttributes.applicationAttributes.relationshipList.subcategory": "Subcategory of the relationship",
  "commonAttributes.applicationAttributes.relationshipType": "Primary relationship type (e.g., client, employee)",
  "commonAttributes.applicationAttributes.statementDate": "Statement date timestamp",
  "commonAttributes.applicationAttributes.subcategory": "Subcategory classification",
  "commonAttributes.archivalJobId": "ID of the archival job if entity is archived",
  "commonAttributes.authorizationAttributes": "Authorization-related attributes",
  "commonAttributes.authorizationAttributes.environment": "Environment information",
  "commonAttributes.authorizationAttributes.environment.name": "Name of the environment attribute",
  "commonAttributes.authorizationAttributes.environment.value": "Value of the environment attribute",
  "commonAttributes.authorizationAttributes.resourceAttributes": "Resource-specific attributes",
  "commonAttributes.authorizationAttributes.resourceAttributes.name": "Name of the resource attribute",
  "commonAttributes.authorizationAttributes.resourceAttributes.value": "Value of the resource attribute",
  "commonAttributes.authorizationAttributes.resourceId": "ID of the resource",
  "commonAttributes.authorizationAttributes.selector": "Selector for authorization",
  "commonAttributes.authorizationAttributes.selector.selectorAttributes": "Attributes of the selector",
  "commonAttributes.authorizationAttributes.selector.selectorAttributes.name": "Name of the selector attribute",
  "commonAttributes.authorizationAttributes.selector.selectorAttributes.value": "Value of the selector attribute",
  "commonAttributes.authorizationAttributes.selector.selectorId": "ID of the selector",
  "commonAttributes.companyRealmId": "Realm ID of the company",
  "commonAttributes.complianceAttributes": "Compliance-related attributes",
  "commonAttributes.complianceAttributes.forbidDelete": "Boolean flag forbidding deletion",
  "commonAttributes.complianceAttributes.forbidUpdate": "Boolean flag forbidding updates",
  "commonAttributes.complianceAttributes.includeInDg2": "Array of data governance actions to include",
  "commonAttributes.complianceAttributes.restrictUpdate": "Boolean flag restricting updates",
  "commonAttributes.credentialSetId": "ID of the credential set",
  "commonAttributes.description": "Human-readable description of the entity",
  "commonAttributes.documentType": "Type/classification of the document (e.g., W2, receipt, invoice, 1099, payroll)",
  "commonAttributes.domainAttributes": "Domain-specific attributes array",
  "commonAttributes.domainAttributes.domain": "Domain name (e.g., BUSINESS, PERSONAL)",
  "commonAttributes.domainAttributes.nameValues": "Name-value pairs for domain attributes",
  "commonAttributes.domainAttributes.nameValues.name": "Name of the domain attribute",
  "commonAttributes.domainAttributes.nameValues.value": "Value of the domain attribute",
  "commonAttributes.import": "Import-related information",
  "commonAttributes.import.sourceImport": "Source of the import",
  "commonAttributes.is7216": "Boolean flag for IRS form 7216 consent",
  "commonAttributes.location": "Geographic location information",
  "commonAttributes.location.address": "Physical address",
  "commonAttributes.location.address.addressLine1": "Address line 1",
  "commonAttributes.location.address.addressLine2": "Address line 2",
  "commonAttributes.location.address.addressLine3": "Address line 3",
  "commonAttributes.location.address.city": "City name",
  "commonAttributes.location.address.country": "Country code",
  "commonAttributes.location.address.state": "State code or name",
  "commonAttributes.location.address.zip": "Zip or postal code",
  "commonAttributes.location.lat": "Latitude coordinate",
  "commonAttributes.location.lng": "Longitude coordinate",
  "commonAttributes.name": "Display name of the entity (e.g., file name)",
  "commonAttributes.notes": "User-added notes for the entity",
  "commonAttributes.notificationAttributes": "Notification settings",
  "commonAttributes.notificationAttributes.destination": "Notification destination",
  "commonAttributes.notificationAttributes.destination.alias": "Alias for the destination",
  "commonAttributes.notificationAttributes.destination.type": "Type of destination (e.g., email, sms)",
  "commonAttributes.notificationAttributes.destination.value": "Value of the destination (e.g., email address)",
  "commonAttributes.offeringAttributes": "Offering-specific attributes array (nested field)",
  "commonAttributes.offeringAttributes.externalAssociations": "External associations for the offering",
  "commonAttributes.offeringAttributes.nameValues": "Name-value pairs for offering attributes",
  "commonAttributes.offeringAttributes.nameValues.name": "Name of the offering attribute",
  "commonAttributes.offeringAttributes.nameValues.value": "Value of the offering attribute",
  "commonAttributes.offeringAttributes.offeringId": "Intuit offering ID (e.g., Intuit.workermgmt.employeemgmt)",
  "commonAttributes.payloadVersion": "Version of the payload schema",
  "commonAttributes.providerId": "ID of the provider",
  "commonAttributes.providerName": "Name of the provider (e.g., Intuit)",
  "commonAttributes.semanticVersion": "Semantic version of the entity schema",
  "commonAttributes.tags": "Array of user-defined tags for the entity",
  "commonAttributes.taxYear": "Tax year associated with the document (e.g., 2023, 2024)",
  "commonAttributes.userConsentRequired": "Boolean flag indicating if user consent is required",
  "commonAttributes.userReviewStatus": "Status of user review",
  "entityType": "Type of entity: DOCUMENT or FOLDER",
  "organizationAttributes": "Organization/folder structure attributes",
  "organizationAttributes.folderPath": "Path to the parent folder (e.g., root, /path/to/folder)",
  "organizationAttributes.folderPathIds": "Array of folder IDs in the path hierarchy",
  "organizationAttributes.parentFolderId": "ID of the parent folder",
  "semanticData": "Extracted semantic data from the document (e.g., W2 fields, invoice data)",
  "systemAttributes": "System-managed attributes",
  "systemAttributes.alternateDataLocators": "Array of alternative data locations",
  "systemAttributes.alternateDataLocators.alternateDataType": "Type of alternate data (e.g., rawSemanticData, desResponseData)",
  "systemAttributes.alternateDataLocators.contentType": "Content type of the alternate data",
  "systemAttributes.alternateDataLocators.locator": "URL/path to the alternate data",
  "systemAttributes.appCreated": "Application that created the entity",
  "systemAttributes.appModified": "Application that last modified the entity",
  "systemAttributes.assetId": "ID of the asset",
  "systemAttributes.channel": "Channel through which the entity was created (e.g., upload, api)",
  "systemAttributes.children": "Child entities",
  "systemAttributes.classificationDetails": "Details about document classification",
  "systemAttributes.classificationDetails.confidenceLevel": "Confidence level of the classification",
  "systemAttributes.classificationDetails.documentType": "Classified document type",
  "systemAttributes.classificationStatus": "Status of document classification",
  "systemAttributes.contentModerationAttribute": "Content moderation attributes",
  "systemAttributes.contentModerationAttribute.minConfidence": "Minimum confidence threshold for moderation",
  "systemAttributes.contentModerationAttribute.modelProviderName": "Name of the moderation model provider",
  "systemAttributes.contentModerationAttribute.moderatedDate": "Date when content was moderated",
  "systemAttributes.contentModerationAttribute.moderatedPages": "Pages that were moderated",
  "systemAttributes.contentModerationAttribute.rejectedPages": "Pages that were rejected",
  "systemAttributes.contentModerationAttribute.rejectedPages.confidence": "Confidence score for rejection",
  "systemAttributes.contentModerationAttribute.rejectedPages.labels": "Labels for rejected content",
  "systemAttributes.contentModerationAttribute.rejectedPages.pageNumber": "Page number that was rejected",
  "systemAttributes.contentModerationStatus": "Status of content moderation (e.g., PENDING, CLEAN, REJECTED)",
  "systemAttributes.copiedFrom": "ID of the original entity if this is a copy",
  "systemAttributes.createDate": "Timestamp when the entity was created (epoch milliseconds)",
  "systemAttributes.createdBy": "User ID who created the entity",
  "systemAttributes.creatorMetadata": "Metadata about the creator",
  "systemAttributes.creatorMetadata.creatorAccountId": "Account ID of the creator",
  "systemAttributes.creatorMetadata.creatorNamespaceId": "Namespace ID of the creator",
  "systemAttributes.creatorMetadata.creatorPersonaId": "Persona ID of the creator",
  "systemAttributes.creatorMetadata.creatorRealmId": "Realm ID of the creator",
  "systemAttributes.creatorMetadata.creatorUserId": "User ID of the creator",
  "systemAttributes.creatorMetadata.creatorUserIdPseudonym": "Pseudonymized user ID of the creator",
  "systemAttributes.dataExtractionStatus": "Status of data extraction (e.g., ASYNC_COMPLETED, PENDING, FAILED)",
  "systemAttributes.entities": "Entities extracted from the document",
  "systemAttributes.entities.dataSource": "Source of the entity data",
  "systemAttributes.entities.entityId": "ID of the extracted entity",
  "systemAttributes.entities.entityType": "Type of the extracted entity",
  "systemAttributes.entities.extractionConfidence": "Confidence score for the extraction",
  "systemAttributes.entities.extractor": "Name of the extractor used",
  "systemAttributes.entitySupported": "Boolean indicating if entity operations are supported",
  "systemAttributes.extractionConfidence": "Overall confidence score for data extraction",
  "systemAttributes.extractor": "Name of the extraction service used (e.g., dup)",
  "systemAttributes.genericDocTypes": "Generic document type classifications",
  "systemAttributes.id": "Unique identifier for the entity (UUID)",
  "systemAttributes.isComposite": "Boolean flag indicating if this is a composite entity",
  "systemAttributes.isTargetState": "Boolean flag indicating if this is a target state",
  "systemAttributes.lastUpdatingAssetId": "Asset ID that last updated this entity",
  "systemAttributes.masterVersion": "Master version timestamp",
  "systemAttributes.modifiedBy": "User ID who last modified the entity",
  "systemAttributes.modifyDate": "Timestamp when the entity was last modified (epoch milliseconds)",
  "systemAttributes.offeringId": "Intuit offering ID that created the entity",
  "systemAttributes.originalDocumentName": "Original file name when uploaded",
  "systemAttributes.originatingAssetId": "Asset ID that originated this entity",
  "systemAttributes.owner": "Owner information for the entity",
  "systemAttributes.owner.authId": "Auth ID of the owner",
  "systemAttributes.owner.authZOwnerId": "AuthZ owner ID",
  "systemAttributes.owner.namespaceId": "Namespace ID of the owner",
  "systemAttributes.owner.ownerAccountId": "Account ID of the owner",
  "systemAttributes.owner.ownerAccountType": "Type of owner account (e.g., REALM, USER)",
  "systemAttributes.owner.realmId": "Realm ID of the owner",
  "systemAttributes.ownerMetadata": "Metadata about the entity owner",
  "systemAttributes.ownerMetadata.accountId": "Account ID in owner metadata",
  "systemAttributes.ownerMetadata.accountType": "Type of account (e.g., realm, user)",
  "systemAttributes.ownerMetadata.contextId": "Context ID for ownership",
  "systemAttributes.ownerMetadata.contextType": "Type of context (e.g., realm)",
  "systemAttributes.ownerMetadata.identifierId": "Identifier ID",
  "systemAttributes.ownerMetadata.identifierType": "Type of identifier",
  "systemAttributes.ownerMetadata.ownershipType": "Type of ownership (e.g., realm)",
  "systemAttributes.parentId": "ID of the parent folder or entity (use 'root' for root level)",
  "systemAttributes.pdfConversionStatus": "Status of PDF conversion",
  "systemAttributes.selfLocator": "URL path to access this entity",
  "systemAttributes.semanticHash": "Hash of the semantic data",
  "systemAttributes.semanticSource": "Source of semantic data (e.g., SYSTEM_GENERATED, USER_PROVIDED)",
  "systemAttributes.signatureAttributes": "Digital signature attributes",
  "systemAttributes.signatureAttributes.envelopeId": "Envelope ID for signatures",
  "systemAttributes.size": "Size of the entity in bytes",
  "systemAttributes.sourceLocators": "Array of source file locations",
  "systemAttributes.sourceLocators.contentModerationStatus": "Moderation status for this source",
  "systemAttributes.sourceLocators.contentType": "MIME type of the source (e.g., image/png, application/pdf)",
  "systemAttributes.sourceLocators.index": "Index of this source in the array",
  "systemAttributes.sourceLocators.largeFile": "Boolean indicating if this is a large file",
  "systemAttributes.sourceLocators.locator": "URL path to access the source file",
  "systemAttributes.sourceLocators.size": "Size of the source file in bytes",
  "systemAttributes.sourceLocators.thumbnailLocators": "Array of thumbnail locations",
  "systemAttributes.sourceLocators.thumbnailLocators.contentType": "Content type of the thumbnail",
  "systemAttributes.sourceLocators.thumbnailLocators.locator": "URL path to the thumbnail",
  "systemAttributes.sourceLocators.thumbnailLocators.thumbnailType": "Type/size of thumbnail (e.g., medium, large, extraLarge)",
  "systemAttributes.sourceLocators.thumbnailPresent": "Boolean indicating if thumbnails are available",
  "systemAttributes.sourceLocators.virusScanStatus": "Virus scan status (e.g., CLEAN, INFECTED, PENDING)",
  "systemAttributes.userCreateDate": "Timestamp when user initiated the creation",
  "systemAttributes.version": "Version string for the entity",
  "usageType": "Type of usage for the entity"
}

# Few-shot examples loaded from Resources/Schemas/FewShotExamples.json
FEW_SHOT_EXAMPLES = [
  {
    "natural_language": "Find all folders for client with relationship ID 9341455527283258, relationship type client, in category _private.qboa, for tax year 2024, with subcategory booksreview, that are not PCI",
    "notes": "Query to search for documents under a specific client",
    "elasticsearch_query": {
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
              "authorization.isPci": False
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
  },
  {
    "natural_language": "Get all documents and folders under parent folder ID 40658d40-8764-4b41-aea6-a6c6450944e6",
    "notes": "Query to search for documents under a specific folder",
    "elasticsearch_query": {
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
  },
  {
    "natural_language": "Find receipts with auth type REALM from offering IDs Intuit.smallbusiness.qbeswarehouse.qbwhandroidapp, Intuit.qbshared.attachments.qbdtreceiptscapturemob, or Intuit.qbshared.attachments.qbdtreceiptscapture, excluding those in reviewed category and those with data extraction status ASYNC_COMPLETED",
    "notes": "Query to search for documents that have specific offering IDs",
    "elasticsearch_query": {
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
  },
  {
    "natural_language": "List all documents and folders in the root folder",
    "notes": "Query to list documents under root folder",
    "elasticsearch_query": {
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
  },
  {
    "natural_language": "Find documents with system ID trigger-elastic-index",
    "notes": "Query to search for documents that have a specific system attribute",
    "elasticsearch_query": {
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
  },
  {
    "natural_language": "Find non-PCI documents with offering ID Intuit.intcollabs.collab.collabvep and external association starting with vep://reqId/557ab504-b291-42f6-9f07-7bd159cdce5d",
    "notes": "Query with nested query for offering attributes",
    "elasticsearch_query": {
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
                    "authorization.isPci": False
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
  }
]


# --- Configuration Constants ---

MODEL_NAME = "claude-sonnet-4-5-20250929"
TEMPERATURE = 0.0
TIMEOUT_SECONDS = 60
MAX_RETRIES = 3
RETRY_DELAYS = [2, 4, 8]  # Exponential backoff in seconds


# --- Helper Functions ---

def _build_llm_prompt(user_query: str) -> str:
    """
    Builds the complete prompt for the LLM including mapping, descriptions, and examples.

    Args:
        user_query: The natural language query from the user

    Returns:
        Complete prompt string
    """
    # Format field descriptions
    descriptions_str = "\n".join([f"- **{k}**: {v}" for k, v in FIELD_DESCRIPTIONS.items()])

    # Format few-shot examples
    examples_str = ""
    for i, example in enumerate(FEW_SHOT_EXAMPLES, 1):
        examples_str += f"\n### Example {i}\n"
        examples_str += f"**Natural Language**: {example['natural_language']}\n\n"
        examples_str += f"**Elasticsearch Query**:\n```json\n{json.dumps(example['elasticsearch_query'], indent=2)}\n```\n"

    prompt = f"""You are an expert Elasticsearch query generator for the entities-v4 index. Your task is to convert natural language search descriptions into syntactically valid Elasticsearch DSL queries.

## Your Task

Convert the user's natural language query into a valid Elasticsearch DSL query for the entities-v4 index.

## Rules

1. **Use Only Valid Fields:** Only use fields that exist in the provided mapping below. Do not invent or assume fields.

2. **Exact Matches:** For text fields that have a .keyword subfield, use the .keyword version for exact matching (e.g., "entityType.keyword" not "entityType").

3. **Field Types:** Respect field types from the mapping:
   - Use `term` for exact matches on keyword/boolean/integer fields
   - Use `match` for full-text search on text fields
   - Use `range` for date/numeric ranges
   - Use `nested` queries for nested object arrays

4. **Query Structure:** Return ONLY the query object itself, not a complete search request. For example:
   ```json
   {{
     "bool": {{
       "must": [...]
     }}
   }}
   ```
   NOT:
   ```json
   {{
     "query": {{
       "bool": {{ ... }}
     }}
   }}
   ```

5. **Ambiguity:** If the query is ambiguous or unclear, respond with:
   ```json
   {{
     "error": "AMBIGUOUS_QUERY",
     "message": "Specific explanation of what is ambiguous and what clarification is needed"
   }}
   ```

6. **Unknown Fields:** If the query asks for fields not in the mapping, respond with:
   ```json
   {{
     "error": "UNSUPPORTED_FIELD",
     "message": "Field(s) not found in mapping: [list fields]"
   }}
   ```

7. **Explicit Only:** Only include filters/conditions that are explicitly mentioned in the user's query. Do NOT add authentication, authorization, or other implicit filters.

8. **Best Practices:**
   - Combine multiple conditions with `bool` queries (must, should, must_not, filter)
   - Use `filter` context for exact matches that don't need scoring
   - Use `must` context when scoring/relevance matters
   - Handle both DOCUMENT and FOLDER entity types appropriately based on the query

## Elasticsearch Mapping

Below is the complete mapping for the entities-v4 index. Refer to this for all field names and types:

```json
{ELASTICSEARCH_MAPPING}
```

## Field Descriptions

The following descriptions explain the semantic meaning of key fields in the mapping:

{descriptions_str}

## Examples

Here are example natural language queries and their corresponding Elasticsearch queries:

{examples_str}

## User Query

Now, convert this natural language query to an Elasticsearch DSL query:

"{user_query}"

## Your Response

Return ONLY valid JSON. Either:
1. A valid Elasticsearch query object, OR
2. An error object with "error" and "message" fields

Do not include any explanatory text outside the JSON."""

    return prompt


def _call_llm_with_retry(prompt: str, api_key: str) -> Dict[str, Any]:
    """
    Calls the Anthropic API with retry logic.

    Args:
        prompt: The complete prompt to send
        api_key: Anthropic API key

    Returns:
        Parsed JSON response from the LLM

    Raises:
        Exception: If all retries fail
    """
    client = Anthropic(api_key=api_key)

    for attempt in range(MAX_RETRIES):
        try:
            response = client.messages.create(
                model=MODEL_NAME,
                max_tokens=4096,
                temperature=TEMPERATURE,
                messages=[
                    {"role": "user", "content": prompt}
                ],
                timeout=TIMEOUT_SECONDS
            )

            # Extract text from response
            response_text = response.content[0].text.strip()

            # Parse JSON from response
            # Handle case where response might be wrapped in ```json blocks
            if response_text.startswith("```json"):
                response_text = response_text.split("```json")[1].split("```")[0].strip()
            elif response_text.startswith("```"):
                response_text = response_text.split("```")[1].split("```")[0].strip()

            parsed_response = json.loads(response_text)
            return parsed_response

        except (APIConnectionError, APIError) as e:
            if attempt < MAX_RETRIES - 1:
                time.sleep(RETRY_DELAYS[attempt])
                continue
            else:
                raise Exception(f"API call failed after {MAX_RETRIES} attempts: {str(e)}")
        except AuthenticationError as e:
            # Don't retry on auth errors
            raise Exception(f"Authentication failed: {str(e)}")
        except json.JSONDecodeError as e:
            # Don't retry on JSON parsing errors - this is a malformed response
            raise Exception(f"Failed to parse LLM response as JSON: {str(e)}")


def _validate_query(query_dict: Dict[str, Any]) -> None:
    """
    Validates an Elasticsearch query using elasticsearch-dsl library.

    Args:
        query_dict: The query dictionary to validate

    Raises:
        Exception: If validation fails
    """
    try:
        # Create a Search object and apply the query
        s = Search()
        s = s.query(Q(query_dict))

        # Attempt to convert to dict (this triggers validation)
        _ = s.to_dict()

    except Exception as e:
        raise Exception(f"Query validation failed: {str(e)}")


# --- Main Tool Function ---

def generate_elasticsearch_query(query: str) -> Dict[str, Any]:
    """
    Generates a syntactically valid Elasticsearch DSL query for the entities-v4 index
    based on a natural language description.

    This tool uses Claude Sonnet 4.5 with embedded mapping information, field descriptions,
    and few-shot examples to translate user queries into proper Elasticsearch DSL queries.

    Args:
        query: Natural language query describing the search requirement.
               Examples: "Fetch my W2's", "Find all documents under FolderId ABC"

    Returns:
        A dictionary containing either:
        - {"elasticsearch_query": <valid ES query object>} on success
        - {"error": <ERROR_CODE>, "message": <description>} on failure

    Error Codes:
        - EMPTY_QUERY: Query parameter is empty or whitespace
        - AMBIGUOUS_QUERY: LLM cannot confidently map the query
        - LLM_API_FAILURE: Anthropic API failed after retries
        - INVALID_API_KEY: ANTHROPIC_API_KEY missing or invalid
        - MALFORMED_RESPONSE: Invalid JSON from LLM
        - VALIDATION_FAILED: Query failed elasticsearch-dsl validation
        - UNSUPPORTED_FIELD: Query references non-existent fields

    Environment Variables:
        ANTHROPIC_API_KEY: Valid Anthropic API key (required)

    Dependencies:
        - anthropic >= 0.18.0
        - elasticsearch-dsl >= 8.0.0
    """
    # Check for empty query
    if not query or not query.strip():
        return {
            "error": "EMPTY_QUERY",
            "message": "Query cannot be empty. Please provide a natural language search description."
        }

    # Check for API key
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        return {
            "error": "INVALID_API_KEY",
            "message": "Anthropic API key is missing or invalid. Please set ANTHROPIC_API_KEY environment variable."
        }

    try:
        # Build the prompt
        prompt = _build_llm_prompt(query.strip())

        # Call LLM with retry logic
        try:
            llm_response = _call_llm_with_retry(prompt, api_key)
        except Exception as e:
            error_msg = str(e)
            if "Authentication" in error_msg or "API key" in error_msg:
                return {
                    "error": "INVALID_API_KEY",
                    "message": f"Anthropic API key is missing or invalid. Please set ANTHROPIC_API_KEY environment variable."
                }
            elif "JSON" in error_msg or "parse" in error_msg:
                return {
                    "error": "MALFORMED_RESPONSE",
                    "message": f"LLM generated an invalid response format: {error_msg}"
                }
            else:
                return {
                    "error": "LLM_API_FAILURE",
                    "message": f"Failed to generate query due to LLM API error: {error_msg}"
                }

        # Check if LLM returned an error
        if "error" in llm_response:
            error_code = llm_response.get("error")
            error_message = llm_response.get("message", "No message provided")

            # Return the error as-is (AMBIGUOUS_QUERY or UNSUPPORTED_FIELD)
            return {
                "error": error_code,
                "message": error_message
            }

        # LLM returned a query - validate it
        try:
            _validate_query(llm_response)
        except Exception as e:
            return {
                "error": "VALIDATION_FAILED",
                "message": f"Generated query failed validation: {str(e)}"
            }

        # Success - return the validated query
        return {
            "elasticsearch_query": llm_response
        }

    except Exception as e:
        # Catch-all for unexpected errors
        return {
            "error": "LLM_API_FAILURE",
            "message": f"An unexpected error occurred: {str(e)}"
        }


# --- Main Entry Point ---

def main():
    """
    Main function to demonstrate the usage of generate_elasticsearch_query when script is run directly.
    """
    import sys

    if len(sys.argv) < 2:
        print("Usage: python generate_elasticsearch_query.py <natural_language_query>")
        print("\nExample:")
        print('  python generate_elasticsearch_query.py "Find all W2 documents"')
        sys.exit(1)

    query = " ".join(sys.argv[1:])
    result = generate_elasticsearch_query(query)

    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
