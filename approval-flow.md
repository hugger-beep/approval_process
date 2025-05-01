``` mermaid
sequenceDiagram
    participant CA as Central Account
    participant MA as Member Account
    participant User as Customer

    rect rgb(191, 223, 255)
        note over CA: Central Account Components
        box rgb(191, 223, 255) Central Account Flow
            participant EB as EventBridge
            participant L1 as Lambda (Email)
            participant SNS as SNS Topic
        end
    end

    rect rgb(200, 255, 200)
        note over MA: Member Account Components
        box rgb(200, 255, 200) Member Account Flow
            participant AG as API Gateway
            participant L2 as Lambda (Verify)
            participant SF as Step Functions
            participant DDB as DynamoDB
        end
    end

    %% Flow
    EB->>L1: Trigger approval flow
    L1->>DDB: Store request ID & token
    L1->>SNS: Send email with signed URLs
    SNS-->>User: Approval email
    
    alt Approve
        User->>AG: Click approval URL with token
        AG->>L2: Forward request
        L2->>DDB: Verify token & request ID
        L2->>SF: Start workflow if valid
        SF-->>User: Success response
    else Reject
        User->>SNS: Click reject URL
        SNS->>L1: Send rejection notification
        L1-->>User: Confirmation email
    end

```


``` mermaid


graph TB
    subgraph "Central Account"
        EB[EventBridge]
        L1[Lambda Email Sender]
        SNS[SNS Topic]
        style L1 fill:#f9f,stroke:#333
        style EB fill:#87CEEB,stroke:#333
        style SNS fill:#FFB6C1,stroke:#333
    end

    subgraph "Member Account"
        APIG[API Gateway]
        L2[Lambda Verifier]
        SF[Step Functions]
        DDB[(DynamoDB<br/>Tokens)]
        style APIG fill:#98FB98,stroke:#333
        style L2 fill:#f9f,stroke:#333
        style SF fill:#DDA0DD,stroke:#333
        style DDB fill:#F0E68C,stroke:#333
    end

    subgraph "External"
        USER[Customer]
        style USER fill:#fff,stroke:#333
    end

    %% Connections
    EB -->|Trigger| L1
    L1 -->|Store Token| DDB
    L1 -->|Send Email| SNS
    SNS -->|Approval Links| USER
    USER -->|Approve| APIG
    USER -->|Reject| SNS
    APIG -->|Verify| L2
    L2 -->|Check Token| DDB
    L2 -->|Start| SF

    %% Connection styles
    classDef connection stroke-width:2px;
    linkStyle default stroke:#333,stroke-width:2px;
```


``` mermaid

graph TB
    subgraph "Central Account"
        EB[EventBridge]
        L1[Email Sender Lambda]
        SNS1[Approval SNS Topic]
        SNS2[Rejection SNS Topic]
        SM[Secrets Manager<br/>Signing Secret]
        KMS1[SNS KMS Key]
        KMS2[Secrets KMS Key]
        style L1 fill:#f9f,stroke:#333
        style EB fill:#87CEEB,stroke:#333
        style SNS1 fill:#FFB6C1,stroke:#333
        style SNS2 fill:#FFB6C1,stroke:#333
        style SM fill:#DDA0DD,stroke:#333
        style KMS1 fill:#F0E68C,stroke:#333
        style KMS2 fill:#F0E68C,stroke:#333
    end

    subgraph "Member Account"
        APIG[API Gateway]
        WAF[WAF Web ACL]
        L2[Verifier Lambda]
        SF[Step Functions]
        DDB[(DynamoDB<br/>Tokens)]
        KMS3[DynamoDB KMS Key]
        CW[CloudWatch Logs]
        style APIG fill:#98FB98,stroke:#333
        style WAF fill:#FFB6C1,stroke:#333
        style L2 fill:#f9f,stroke:#333
        style SF fill:#DDA0DD,stroke:#333
        style DDB fill:#F0E68C,stroke:#333
        style KMS3 fill:#F0E68C,stroke:#333
        style CW fill:#87CEEB,stroke:#333
    end

    subgraph "External"
        USER[Customer]
        IP[Allowed IP CIDR]
        style USER fill:#fff,stroke:#333
        style IP fill:#fff,stroke:#333
    end

    %% Central Account Connections
    EB -->|Schedule| L1
    L1 -->|Assume Role| DDB
    L1 -->|Get Secret| SM
    L1 -->|Send Approval| SNS1
    L1 -->|Send Rejection| SNS2
    KMS1 -->|Encrypt| SNS1
    KMS1 -->|Encrypt| SNS2
    KMS2 -->|Encrypt| SM

    %% Member Account Connections
    IP -->|Allow| WAF
    WAF -->|Protect| APIG
    APIG -->|Invoke| L2
    L2 -->|Verify| DDB
    L2 -->|Get Secret| SM
    L2 -->|Start| SF
    KMS3 -->|Encrypt| DDB
    L2 -->|Log| CW
    SF -->|Log| CW

    %% User Interactions
    SNS1 -->|Approval Link| USER
    SNS2 -->|Rejection Link| USER
    USER -->|Approve/Reject| APIG

    %% Connection styles
    classDef connection stroke-width:2px;
    linkStyle default stroke:#333,stroke-width:2px;
```
