
``` mermaid

flowchart TD
    subgraph "Lambda Handler Flow"
        Start([Lambda Start]) --> ValidateParams[Validate Request Parameters]
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
        SecretsManager[(Secrets Manager)]
        DynamoDB[(DynamoDB)]
        SNSTopic[(SNS Topic)]
        CloudWatch[(CloudWatch Logs)]
    end

    subgraph "Helper Functions"
        direction TB
        GetSecret[Get Signing Secret]
        ValidateReq[Validate Request Parameters]
        VerifySign[Verify Signature]
        UpdateDB[Update DynamoDB]
        SendNotif[Send SNS Notification]
        GenHTML[Generate HTML Response]
    end

    subgraph "Parameter Validation"
        direction LR
        CheckToken[Check Token]
        CheckSig[Check Signature]
        CheckTime[Check Timestamp]
    end

    subgraph "HTML Response Types"
        SuccessHTML[Success Template]
        ErrorHTML[Error Template]
    end

    %% Service Connections
    VerifySig -.->|Fetch Secret| SecretsManager
    UpdateDDB -.->|Update Token Status| DynamoDB
    SendSNS -.->|Send Approval Message| SNSTopic
    Lambda -.->|Log Events| CloudWatch

    %% Function Dependencies
    ValidateParams --> CheckToken & CheckSig & CheckTime
    VerifySig -.->|Uses| GetSecret
    UpdateDDB -.->|Uses| UpdateDB
    SendSNS -.->|Uses| SendNotif
    GenResponse -.->|Uses| GenHTML
    GenHTML -->|Success| SuccessHTML
    GenHTML -->|Error| ErrorHTML

    %% Error Handling Paths
    Error1 -->|400 Bad Request| Return
    Error2 -->|401 Unauthorized| Return
    Error3 -->|500 Server Error| Return
    Error4 -->|500 Server Error| Return

    %% Styling
    classDef awsService fill:#FF9900,stroke:#232F3E,stroke-width:2px,color:white;
    classDef function fill:#87CEEB,stroke:#232F3E,stroke-width:2px;
    classDef validation fill:#98FB98,stroke:#232F3E,stroke-width:2px;
    classDef error fill:#FF6B6B,stroke:#232F3E,stroke-width:2px;
    classDef html fill:#DDA0DD,stroke:#232F3E,stroke-width:2px;
    classDef flow fill:#F0E68C,stroke:#232F3E,stroke-width:2px;

    class SecretsManager,DynamoDB,SNSTopic,CloudWatch awsService;
    class GetSecret,ValidateReq,VerifySign,UpdateDB,SendNotif,GenHTML function;
    class CheckToken,CheckSig,CheckTime validation;
    class Error1,Error2,Error3,Error4 error;
    class SuccessHTML,ErrorHTML html;
    class Start,Return,ValidateParams,VerifySig,UpdateDDB,SendSNS,GenResponse flow;
```
