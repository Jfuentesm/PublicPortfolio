// Mock data for AIRisk Demo

// User data
const currentUser = {
    id: 1,
    name: 'John Smith',
    email: 'john.smith@example.com',
    role: 'Administrator',
    department: 'Executive',
    avatar: 'JS'
};

// Company data
const companyProfile = {
    name: 'Acme Inc.',
    industry: 'Technology / Software',
    size: 'Medium (100-250 employees)',
    location: 'United States',
    keyOperations: ['Software Development', 'Cloud Services'],
    complianceRequirements: ['GDPR', 'CCPA', 'SOC 2']
};

// Risk data
const risks = [
    {
        id: 1,
        title: 'Data Breach Risk',
        category: 'Cybersecurity',
        description: 'Risk of unauthorized access to sensitive customer data due to inadequate security controls.',
        owner: 'Sarah Johnson',
        ownerId: 2,
        status: 'Active',
        likelihood: 4,
        impact: 5,
        score: 20,
        priority: 'High',
        aiLikelihood: 4,
        aiImpact: 5,
        aiJustification: 'Recent industry trends show increasing frequency of attacks on similar companies. Your current security posture has some gaps in multi-factor authentication and endpoint protection.',
        createdAt: '2025-03-15',
        updatedAt: '2025-04-10'
    },
    {
        id: 2,
        title: 'Supply Chain Disruption',
        category: 'Operational',
        description: 'Risk of business interruption due to key supplier failure or logistics issues.',
        owner: 'Michael Chen',
        ownerId: 3,
        status: 'Active',
        likelihood: 4,
        impact: 4,
        score: 16,
        priority: 'High',
        aiLikelihood: 3,
        aiImpact: 4,
        aiJustification: 'Your company relies on several key suppliers with limited alternatives. Recent global events have increased supply chain volatility.',
        createdAt: '2025-03-18',
        updatedAt: '2025-04-10'
    },
    {
        id: 3,
        title: 'Regulatory Non-Compliance',
        category: 'Compliance',
        description: 'Risk of penalties due to failure to comply with industry regulations.',
        owner: 'Lisa Rodriguez',
        ownerId: 4,
        status: 'Active',
        likelihood: 3,
        impact: 5,
        score: 15,
        priority: 'High',
        aiLikelihood: 3,
        aiImpact: 5,
        aiJustification: 'Your industry is subject to evolving regulations, and your compliance program has some gaps in monitoring and documentation.',
        createdAt: '2025-03-20',
        updatedAt: '2025-04-10'
    },
    {
        id: 4,
        title: 'Key Personnel Departure',
        category: 'Human Resources',
        description: 'Risk of knowledge loss and operational disruption due to departure of key employees.',
        owner: 'John Smith',
        ownerId: 1,
        status: 'Active',
        likelihood: 3,
        impact: 4,
        score: 12,
        priority: 'Medium',
        aiLikelihood: 3,
        aiImpact: 4,
        aiJustification: 'Your company has several key roles with specialized knowledge and limited documentation or knowledge transfer processes.',
        createdAt: '2025-03-22',
        updatedAt: '2025-04-10'
    },
    {
        id: 5,
        title: 'Market Share Decline',
        category: 'Strategic',
        description: 'Risk of losing market position due to new competitors or changing customer preferences.',
        owner: 'John Smith',
        ownerId: 1,
        status: 'Active',
        likelihood: 3,
        impact: 4,
        score: 12,
        priority: 'Medium',
        aiLikelihood: 3,
        aiImpact: 4,
        aiJustification: 'Market analysis shows increasing competition and evolving customer needs in your sector.',
        createdAt: '2025-03-25',
        updatedAt: '2025-04-10'
    }
];

// Risk library (standard risks by category)
const riskLibrary = {
    cybersecurity: [
        {
            title: 'Data Breach',
            description: 'Unauthorized access to sensitive customer or business data due to inadequate security controls.'
        },
        {
            title: 'Ransomware Attack',
            description: 'Malicious software that encrypts company data and demands payment for decryption keys.'
        },
        {
            title: 'Phishing Attacks',
            description: 'Social engineering attacks targeting employees to gain unauthorized access to systems or data.'
        },
        {
            title: 'Cloud Security Vulnerabilities',
            description: 'Security gaps in cloud infrastructure leading to potential data exposure or service disruption.'
        },
        {
            title: 'Insider Threats',
            description: 'Malicious or negligent actions by employees or contractors with access to sensitive systems.'
        }
    ],
    operational: [
        {
            title: 'Supply Chain Disruption',
            description: 'Interruption in the flow of goods or services due to supplier issues or logistics problems.'
        },
        {
            title: 'Business Continuity Failure',
            description: 'Inability to maintain critical operations during or after a disruptive event.'
        },
        {
            title: 'Technology Infrastructure Failure',
            description: 'Critical system outages or failures impacting business operations.'
        },
        {
            title: 'Process Inefficiencies',
            description: 'Suboptimal operational processes leading to increased costs or reduced productivity.'
        },
        {
            title: 'Quality Control Issues',
            description: 'Defects or inconsistencies in products or services affecting customer satisfaction.'
        }
    ],
    financial: [
        {
            title: 'Cash Flow Shortage',
            description: 'Insufficient liquid assets to meet short-term financial obligations.'
        },
        {
            title: 'Credit Risk',
            description: 'Risk of financial loss due to customers failing to meet payment obligations.'
        },
        {
            title: 'Foreign Exchange Volatility',
            description: 'Financial impact due to unfavorable currency exchange rate movements.'
        },
        {
            title: 'Interest Rate Fluctuations',
            description: 'Financial impact due to changes in interest rates affecting debt servicing costs.'
        },
        {
            title: 'Inadequate Insurance Coverage',
            description: 'Insufficient insurance to cover potential losses or liabilities.'
        }
    ],
    strategic: [
        {
            title: 'Market Share Decline',
            description: 'Loss of competitive position due to new entrants or changing customer preferences.'
        },
        {
            title: 'Failed Product Launch',
            description: 'New product or service fails to meet market expectations or financial targets.'
        },
        {
            title: 'Unsuccessful Merger/Acquisition',
            description: 'Failure to achieve expected benefits from corporate transactions.'
        },
        {
            title: 'Disruptive Technology',
            description: 'Emergence of new technologies that threaten existing business model.'
        },
        {
            title: 'Reputational Damage',
            description: 'Harm to company image affecting customer trust, sales, and stakeholder relationships.'
        }
    ],
    compliance: [
        {
            title: 'Regulatory Non-Compliance',
            description: 'Failure to comply with laws, regulations, or industry standards resulting in penalties.'
        },
        {
            title: 'Data Privacy Violations',
            description: 'Improper handling of personal data leading to regulatory penalties and reputational damage.'
        },
        {
            title: 'Intellectual Property Infringement',
            description: 'Unauthorized use of patents, trademarks, or copyrights leading to legal action.'
        },
        {
            title: 'Environmental Compliance Failure',
            description: 'Non-compliance with environmental regulations resulting in fines or operational restrictions.'
        },
        {
            title: 'Labor Law Violations',
            description: 'Failure to comply with employment regulations resulting in penalties and reputational damage.'
        }
    ]
};

// Mitigation tasks
const mitigationTasks = [
    {
        id: 1,
        title: 'Implement Multi-Factor Authentication',
        description: 'Implement multi-factor authentication for all user accounts in the system to reduce the risk of unauthorized access.',
        riskId: 1,
        riskTitle: 'Data Breach Risk',
        owner: 'John Smith',
        ownerId: 1,
        dueDate: '2025-05-15',
        status: 'In Progress',
        progress: 60,
        createdAt: '2025-04-01'
    },
    {
        id: 2,
        title: 'Update Data Protection Policy',
        description: 'Review and update the data protection policy to ensure compliance with latest regulations and best practices.',
        riskId: 1,
        riskTitle: 'Data Breach Risk',
        owner: 'John Smith',
        ownerId: 1,
        dueDate: '2025-06-10',
        status: 'Not Started',
        progress: 0,
        createdAt: '2025-04-01'
    },
    {
        id: 3,
        title: 'Develop Backup Supplier List',
        description: 'Identify and qualify alternative suppliers for critical components to mitigate supply chain disruption risk.',
        riskId: 2,
        riskTitle: 'Supply Chain Disruption',
        owner: 'John Smith',
        ownerId: 1,
        dueDate: '2025-05-20',
        status: 'In Progress',
        progress: 40,
        createdAt: '2025-04-02'
    },
    {
        id: 4,
        title: 'Review Compliance Requirements',
        description: 'Conduct a comprehensive review of all applicable regulations and assess current compliance status.',
        riskId: 3,
        riskTitle: 'Regulatory Non-Compliance',
        owner: 'John Smith',
        ownerId: 1,
        dueDate: '2025-04-30',
        status: 'Overdue',
        progress: 20,
        createdAt: '2025-04-03'
    },
    {
        id: 5,
        title: 'Document Critical Processes',
        description: 'Create detailed documentation for all critical business processes to reduce dependency on key personnel.',
        riskId: 4,
        riskTitle: 'Key Personnel Departure',
        owner: 'John Smith',
        ownerId: 1,
        dueDate: '2025-05-05',
        status: 'Completed',
        progress: 100,
        createdAt: '2025-04-04',
        completedAt: '2025-04-15'
    },
    {
        id: 6,
        title: 'Conduct Market Analysis',
        description: 'Perform detailed market analysis to identify emerging trends and changing customer preferences.',
        riskId: 5,
        riskTitle: 'Market Share Decline',
        owner: 'John Smith',
        ownerId: 1,
        dueDate: '2025-06-15',
        status: 'Not Started',
        progress: 0,
        createdAt: '2025-04-05'
    }
];

// AI-suggested mitigation actions for Data Breach Risk
const aiSuggestedMitigationActions = [
    {
        title: 'Implement Multi-Factor Authentication',
        description: 'Require MFA for all user accounts, especially those with administrative privileges.',
        owner: 'IT Security Manager',
        dueDate: '2025-05-15',
        priority: 'High'
    },
    {
        title: 'Conduct Security Awareness Training',
        description: 'Provide regular security training to all employees on recognizing and responding to security threats.',
        owner: 'HR Director',
        dueDate: '2025-05-30',
        priority: 'Medium'
    },
    {
        title: 'Update Data Protection Policy',
        description: 'Review and update data protection policies to align with current regulations and best practices.',
        owner: 'Compliance Officer',
        dueDate: '2025-06-10',
        priority: 'Medium'
    },
    {
        title: 'Perform Penetration Testing',
        description: 'Conduct regular penetration testing to identify and address security vulnerabilities.',
        owner: 'IT Security Manager',
        dueDate: '2025-06-30',
        priority: 'High'
    }
];

// Users
const users = [
    {
        id: 1,
        name: 'John Smith',
        email: 'john.smith@example.com',
        role: 'Administrator',
        department: 'Executive'
    },
    {
        id: 2,
        name: 'Sarah Johnson',
        email: 'sarah.johnson@example.com',
        role: 'IT Security Manager',
        department: 'IT'
    },
    {
        id: 3,
        name: 'Michael Chen',
        email: 'michael.chen@example.com',
        role: 'Operations Director',
        department: 'Operations'
    },
    {
        id: 4,
        name: 'Lisa Rodriguez',
        email: 'lisa.rodriguez@example.com',
        role: 'Compliance Officer',
        department: 'Legal'
    }
];

// Recent activity
const recentActivity = [
    {
        type: 'task_completed',
        description: 'Task Completed: Implement Multi-Factor Authentication',
        timestamp: 'Today, 10:23 AM'
    },
    {
        type: 'risk_added',
        description: 'New Risk Added: Market Share Decline',
        timestamp: 'Yesterday, 3:45 PM'
    },
    {
        type: 'risk_updated',
        description: 'Risk Score Updated: Data Breach Risk (15 → 20)',
        timestamp: 'Yesterday, 2:30 PM'
    },
    {
        type: 'plan_created',
        description: 'Mitigation Plan Created: Supply Chain Disruption',
        timestamp: 'Apr 15, 11:20 AM'
    },
    {
        type: 'user_added',
        description: 'User Added: Sarah Johnson (IT Security Manager)',
        timestamp: 'Apr 14, 9:15 AM'
    }
];

// Dashboard metrics
const dashboardMetrics = {
    totalRisks: 38,
    highRisks: 5,
    activeTasks: 12,
    completedTasks: 24,
    risksByCategory: {
        Cybersecurity: 12,
        Operational: 8,
        Financial: 6,
        Strategic: 5,
        Compliance: 4,
        Reputational: 3
    },
    riskTrend: {
        months: ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun'],
        highRisks: [12, 10, 11, 8, 7, 5],
        mediumRisks: [8, 9, 10, 12, 11, 10],
        lowRisks: [5, 6, 8, 9, 10, 12]
    },
    mitigationProgress: {
        categories: ['Cybersecurity', 'Operational', 'Financial', 'Strategic', 'Compliance'],
        completed: [8, 5, 4, 2, 3],
        inProgress: [3, 2, 1, 2, 1],
        notStarted: [1, 1, 1, 1, 0]
    }
};
