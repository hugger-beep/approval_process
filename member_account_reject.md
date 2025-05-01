
``` mermaid

flowchart TD
    subgraph "Lambda Function Flow"
        Start([Start]) --> ValidateParams[Validate Request Parameters]
        ValidateParams -->|Valid| VerifySig[Verify Signature]
        ValidateParams -->|Invalid| Error1[Return 400 Error]
        
        VerifySig -->|Valid| UpdateDDB[Update DynamoDB Status]
        VerifySig -->|Invalid| Error2[Return 401 Error]
        
        UpdateDDB -->|Success| SendSNS[Send SNS Notification]
        UpdateDDB -->|Error| Error3[Return 500 Error]
        
        SendSNS -->|Success| GenResponse[Generate HTML Response]
        SendSNS -->|Error| Error4[Return 500 Error]
        
        GenResponse --> Return([Return Response])
    end

    subgraph "AWS Services"
        SecretsManager[(AWS Secrets Manager)]
        DynamoDB[(DynamoDB)]
        SNSTopic[(SNS Topic)]
    end

    subgraph "Helper Functions"
        GetSecret[Get Signing Secret]
        ValidateReq[Validate Request]
        VerifySign[Verify Signature]
        UpdateDB[Update DynamoDB]
        SendNotif[Send Notification]
        GenHTML[Generate HTML]
    end

    %% Connections
    VerifySig -.->|Get Secret| SecretsManager
    UpdateDDB -.->|Update Status| DynamoDB
    SendSNS -.->|Send Message| SNSTopic

    %% Function Dependencies
    VerifySig -.->|Uses| GetSecret
    ValidateParams -.->|Uses| ValidateReq
    UpdateDDB -.->|Uses| UpdateDB
    SendSNS -.->|Uses| SendNotif
    GenResponse -.->|Uses| GenHTML

    %% Error Handling
    Error1 -->|400| Return
    Error2 -->|401| Return
    Error3 -->|500| Return
    Error4 -->|500| Return

    %% Styling
    classDef awsService fill:#FF9900,stroke:#232F3E,stroke-width:2px,color:white;
    classDef function fill:#87CEEB,stroke:#232F3E,stroke-width:2px;
    classDef error fill:#FF6B6B,stroke:#232F3E,stroke-width:2px;
    classDef flow fill:#98FB98,stroke:#232F3E,stroke-width:2px;

    class SecretsManager,DynamoDB,SNSTopic awsService;
    class GetSecret,ValidateReq,VerifySign,UpdateDB,SendNotif,GenHTML function;
    class Error1,Error2,Error3,Error4 error;
    class Start,Return,ValidateParams,VerifySig,UpdateDDB,SendSNS,GenResponse flow;
```
