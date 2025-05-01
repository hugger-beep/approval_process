``` mermaid

flowchart TD
    subgraph "Central Account"
        SNS[SNS Topics]
        KMS[KMS Keys]
        SM[Secrets Manager]
        Lambda[Email Sender Lambda]
        CW[CloudWatch Logs]
        
        subgraph "KMS Keys"
            SK[Secrets Encryption Key]
            SNSK[SNS Encryption Key]
        end
        
        subgraph "SNS Topics"
            AT[Approval Topic]
            RT[Rejection Topic]
        end
    end
    
    subgraph "Member Account"
        API[API Gateway]
        DDB[DynamoDB Table]
    end
    
    subgraph "External"
        SEC[Security Team]
        USR[Users]
    end

    %% Connections and Flow
    EventBridge -->|Triggers Daily| Lambda
    Lambda -->|Stores Token| DDB
    Lambda -->|Gets Secret| SM
    Lambda -->|Sends Notification| SNS
    
    SK -->|Encrypts| SM
    SNSK -->|Encrypts| SNS
    
    SNS -->|Approval Email| USR
    RT -->|Rejection Notice| SEC
    
    USR -->|Approve/Reject| API
    API -->|Verify Token| DDB
    
    %% Styling
    classDef aws fill:#FF9900,stroke:#232F3E,stroke-width:2px,color:white;
    classDef external fill:#85BBF0,stroke:#232F3E,stroke-width:2px,color:black;
    
    class SNS,KMS,SM,Lambda,CW,API,DDB aws;
    class SEC,USR external;
```
