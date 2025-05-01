``` mermaid

graph TD
    subgraph "API Gateway & WAF"
        APIGW[API Gateway]
        WAF[WAF Web ACL]
        IPSet[IP Set]
        WAFRules[WAF Rules]
        
        WAF -->|Associates with| APIGW
        IPSet -->|Used by| WAFRules
        WAFRules -->|Enforced by| WAF
    end

    subgraph "DynamoDB & KMS"
        DDB[DynamoDB Table<br/>approval-tokens]
        DDBKMS[DynamoDB KMS Key]
        DDBAlias[KMS Key Alias]
        
        DDBKMS -->|Encrypts| DDB
        DDBAlias -->|Points to| DDBKMS
    end

    subgraph "SNS & KMS"
        SNSApproval[Approval Topic]
        SNSReject[Rejection Topic]
        SNSKMS[SNS KMS Key]
        SNSAlias[KMS Key Alias]
        
        SNSKMS -->|Encrypts| SNSApproval
        SNSKMS -->|Encrypts| SNSReject
        SNSAlias -->|Points to| SNSKMS
    end

    subgraph "Secrets Manager"
        Secret[Signing Secret]
        SecretKMS[Secrets KMS Key]
        SecretAlias[KMS Key Alias]
        
        SecretKMS -->|Encrypts| Secret
        SecretAlias -->|Points to| SecretKMS
    end

    subgraph "Lambda Functions"
        ApprovalFn[Approval Function]
        RejectFn[Rejection Function]
        LambdaRole[Lambda Execution Role]
        
        LambdaRole -->|Assumed by| ApprovalFn
        LambdaRole -->|Assumed by| RejectFn
    end

    subgraph "API Resources"
        ApproveRes[/approve Resource]
        RejectRes[/reject Resource]
        
        APIGW -->|Contains| ApproveRes
        APIGW -->|Contains| RejectRes
        ApproveRes -->|Integrates with| ApprovalFn
        RejectRes -->|Integrates with| RejectFn
    end

    subgraph "Cross-Account Access"
        CrossAccRole[Cross Account Role]
        CentralAcct[Central Account]
        
        CentralAcct -->|Assumes| CrossAccRole
        CrossAccRole -->|Accesses| DDB
    end

    subgraph "Logging"
        APILogs[API Gateway Logs]
        WAFLogs[WAF Logs]
        CWLogs[CloudWatch Log Groups]
        
        APIGW -->|Logs to| APILogs
        WAF -->|Logs to| WAFLogs
        APILogs & WAFLogs -->|Stored in| CWLogs
    end

    %% Connections between subgraphs
    ApprovalFn -->|Writes to| DDB
    RejectFn -->|Writes to| DDB
    ApprovalFn -->|Publishes to| SNSApproval
    RejectFn -->|Publishes to| SNSReject
    ApprovalFn & RejectFn -->|Uses| Secret

    %% Styling
    classDef aws fill:#FF9900,stroke:#232F3E,stroke-width:2px,color:white;
    classDef security fill:#DD3522,stroke:#232F3E,stroke-width:2px,color:white;
    classDef logging fill:#3B48CC,stroke:#232F3E,stroke-width:2px,color:white;
    classDef iam fill:#C925D1,stroke:#232F3E,stroke-width:2px,color:white;

    class APIGW,DDB,SNSApproval,SNSReject,ApprovalFn,RejectFn aws;
    class WAF,IPSet,WAFRules,DDBKMS,SNSKMS,SecretKMS security;
    class APILogs,WAFLogs,CWLogs logging;
    class LambdaRole,CrossAccRole iam;
```
