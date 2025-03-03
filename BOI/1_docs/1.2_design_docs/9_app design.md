# Comprehensive Front-End Design for BOI Compliance Management Platform

## 1. DESIGN SYSTEM

### Color Palette
- **Primary**: Navy Blue (#0A2463) - Conveys trust, security, and professionalism
- **Secondary**: Teal (#008891) - Modern accent for interactive elements
- **Tertiary**: Steel Gray (#6C757D) - For secondary texts and UI elements
- **Neutrals**: White (#FFFFFF), Light Gray (#F8F9FA), Medium Gray (#E9ECEF), Dark Gray (#343A40)
- **Alert Colors**:
  - Success: Green (#28A745)
  - Warning: Amber (#FFC107)
  - Error: Red (#DC3545)
  - Info: Light Blue (#17A2B8)
- **Data Sensitivity Indicators**:
  - High Sensitivity: Red accent (#F8D7DA border)
  - Medium Sensitivity: Yellow accent (#FFF3CD border)
  - Standard Data: Blue accent (#D1ECF1 border)

### Typography
- **Primary Font**: SF Pro Display/Roboto/Segoe UI (system stack for optimal loading)
- **Secondary Font**: SF Pro Text/Roboto/Segoe UI
- **Heading Sizes**:
  - H1: 32px/2rem (mobile: 28px/1.75rem)
  - H2: 24px/1.5rem (mobile: 22px/1.375rem)
  - H3: 20px/1.25rem (mobile: 18px/1.125rem)
  - H4: 18px/1.125rem (mobile: 16px/1rem)
- **Body Text**: 16px/1rem (mobile: 15px/0.9375rem)
- **Small Text/Captions**: 14px/0.875rem
- **Line Height**: 1.5 for body text, 1.2 for headings

### Component Library Recommendations
- **Base Framework**: Material UI or Chakra UI (for React), Angular Material (for Angular)
- **Custom Components**:
  - Compliance Status Indicator (with clear visual states)
  - PII Data Field (with sensitivity indicators)
  - Document Upload Zone (with encryption status)
  - Audit Trail Timeline
  - Filing Status Tracker
  - Authentication Components (MFA, biometric indicators)
  - Permission Badges

### Accessibility Considerations
- WCAG 2.1 AA compliance minimum (AAA where possible)
- Minimum contrast ratio of 4.5:1 for normal text, 3:1 for large text
- Focus indicators for keyboard navigation
- Screen reader support with ARIA labels
- Color not used as the sole means of conveying information
- Support for text resizing up to 200% without loss of functionality
- Keyboard accessible navigation and controls

## 2. WEB APPLICATION DESIGN

### Information Architecture (Site Map)
```
Home/Dashboard
├── BOI Filings
│   ├── Filing History
│   ├── Create New Filing
│   │   ├── Reporting Company Information
│   │   ├── Beneficial Owners
│   │   └── Certification & Submission
│   └── Filing Status Tracking
├── Entity Management
│   ├── Reporting Companies List
│   ├── Company Details
│   └── Company Documents
├── Beneficial Owners
│   ├── Owners List
│   ├── Owner Details
│   └── Relationship Visualization
├── Document Management
│   ├── All Documents
│   ├── Document Categories
│   └── Upload New Document
├── User Management (Admin only)
│   ├── User List
│   ├── Roles & Permissions
│   └── Activity Logs
└── Account Settings
    ├── Profile Settings
    ├── Security Settings
    ├── Notification Preferences
    └── API Access (if applicable)
```

### Key Screen Mockups

#### Dashboard
```
+-------------------------------------------------------+
| [Logo] BOI Compliance Platform       [User] [Logout]  |
+-------------------------------------------------------+
| [Sidebar]  |  Dashboard                                |
|            |                                          |
| Dashboard  |  +------------------+ +------------------+|
| BOI Filings|  | Filing Status    | | Recent Activity  ||
| Entities   |  | [Status Cards]   | | [Timeline]       ||
| Owners     |  +------------------+ +------------------+|
| Documents  |                                          |
| Users      |  +------------------+ +------------------+|
| Settings   |  | Upcoming         | | Compliance       ||
|            |  | Deadlines        | | Overview         ||
|            |  | [Calendar]       | | [Charts]         ||
|            |  +------------------+ +------------------+|
|            |                                          |
|            |  +---------------------------------------+|
|            |  | Quick Actions                         ||
|            |  | [New Filing] [Upload Doc] [Add Owner] ||
|            |  +---------------------------------------+|
+------------+------------------------------------------+
```

#### BOI Filing Form
```
+-------------------------------------------------------+
| [Logo] BOI Compliance Platform       [User] [Logout]  |
+-------------------------------------------------------+
| [Sidebar]  |  New BOI Filing > Step 2: Beneficial     |
|            |  Owners                                  |
|            |                                          |
| Dashboard  |  +---------------------------------------+|
| BOI Filings|  | Filing Progress                       ||
| Entities   |  | [Step 1] → [Step 2] → [Step 3]        ||
| Owners     |  +---------------------------------------+|
| Documents  |                                          |
| Users      |  +---------------------------------------+|
| Settings   |  | Beneficial Owner Information          ||
|            |  | [Add sensitivity indicators]          ||
|            |  |                                       ||
|            |  | Name: [   ] [   ] [   ]              ||
|            |  |       First  Middle Last              ||
|            |  |                                       ||
|            |  | DOB: [Date Picker]                    ||
|            |  |                                       ||
|            |  | Address: [   ]                        ||
|            |  |          [   ]                        ||
|            |  |                                       ||
|            |  | ID Number: [   ]                      ||
|            |  | ID Type: [Dropdown]                   ||
|            |  |                                       ||
|            |  | Upload ID Document: [Upload Button]   ||
|            |  |                                       ||
|            |  | Ownership %: [   ]                    ||
|            |  |                                       ||
|            |  | + Add Another Owner                   ||
|            |  |                                       ||
|            |  | [Back] [Save Draft] [Continue]        ||
|            |  +---------------------------------------+|
+------------+------------------------------------------+
```

#### Document Management
```
+-------------------------------------------------------+
| [Logo] BOI Compliance Platform       [User] [Logout]  |
+-------------------------------------------------------+
| [Sidebar]  |  Document Management                      |
|            |                                          |
| Dashboard  |  +---------------------------------------+|
| BOI Filings|  | [Filter] [Search] [Upload] [Sort By ▼]||
| Entities   |  +---------------------------------------+|
| Owners     |                                          |
| Documents  |  +---------------------------------------+|
| Users      |  | All Documents (42)                    ||
| Settings   |  |                                       ||
|            |  | +------------+ +------------+         ||
|            |  | | [Icon] ID   | | [Icon]     |        ||
|            |  | | Document    | | Company    |        ||
|            |  | | John Smith  | | Certificate|        ||
|            |  | | [Sensitive] | | ABC Corp   |        ||
|            |  | +------------+ +------------+         ||
|            |  |                                       ||
|            |  | +------------+ +------------+         ||
|            |  | | [Icon]      | | [Icon]     |        ||
|            |  | | Passport    | | Ownership  |        ||
|            |  | | Jane Doe    | | Agreement  |        ||
|            |  | | [Sensitive] | | [Sensitive]|        ||
|            |  | +------------+ +------------+         ||
|            |  |                                       ||
|            |  | [Load More]                          ||
|            |  +---------------------------------------+|
+------------+------------------------------------------+
```

#### User Management
```
+-------------------------------------------------------+
| [Logo] BOI Compliance Platform       [User] [Logout]  |
+-------------------------------------------------------+
| [Sidebar]  |  User Management                          |
|            |                                          |
| Dashboard  |  +---------------------------------------+|
| BOI Filings|  | [Search] [Add User] [Export] [Filter] ||
| Entities   |  +---------------------------------------+|
| Owners     |                                          |
| Documents  |  +---------------------------------------+|
| Users      |  | Users (15)                            ||
| Settings   |  |                                       ||
|            |  | +-----------------------------------+ ||
|            |  | | Name     | Role       | Status    | ||
|            |  | |------------------------------------|+|
|            |  | | John D.  | Admin      | Active    | ||
|            |  | | Sarah K. | Compliance | Active    | ||
|            |  | | Mike T.  | User       | Inactive  | ||
|            |  | | Lisa M.  | User       | Pending   | ||
|            |  | |          |            |           | ||
|            |  | | [1][2][3][...][10] < >            | ||
|            |  | +-----------------------------------+ ||
|            |  +---------------------------------------+|
+------------+------------------------------------------+
```

### Component Hierarchy

```
<App>
  ├── <AuthProvider>
  ├── <Layout>
  │   ├── <Header>
  │   │   ├── <Logo />
  │   │   ├── <Navigation />
  │   │   └── <UserMenu />
  │   ├── <Sidebar>
  │   │   └── <SidebarNavigation />
  │   ├── <MainContent>
  │   │   └── <Router> (routes to page components)
  │   └── <Footer />
  └── <Modals> (global modal container)

<Page Components>
  ├── <Dashboard>
  │   ├── <StatusSummary />
  │   ├── <ActivityTimeline />
  │   ├── <DeadlineCalendar />
  │   ├── <ComplianceChart />
  │   └── <QuickActions />
  ├── <BOIFilingForm>
  │   ├── <StepProgress />
  │   ├── <FormSection>
  │   │   ├── <SensitiveDataField />
  │   │   ├── <DocumentUpload />
  │   │   └── <ValidationMessage />
  │   └── <FormNavigation />
  ├── <DocumentManagement>
  │   ├── <DocumentFilter />
  │   ├── <DocumentGrid>
  │   │   └── <DocumentCard>
  │   │       ├── <DocumentIcon />
  │   │       ├── <SensitivityBadge />
  │   │       └── <DocumentActions />
  │   └── <UploadModal />
  └── <UserManagement>
      ├── <UserTable>
      │   └── <UserRow>
      ├── <UserForm />
      └── <PermissionMatrix />
```

### Responsive Design Considerations
- Fluid layout using CSS Grid and Flexbox
- Breakpoints:
  - Mobile: 320px - 767px
  - Tablet: 768px - 1023px
  - Desktop: 1024px+
- Collapsible sidebar for tablet and mobile views
- Stacked card layout for dashboards in mobile view
- Simplified tables with horizontal scrolling for mobile
- Touch-friendly UI elements (minimum 44px × 44px touch targets)
- Form layouts that adapt from multi-column (desktop) to single column (mobile)
- Optimized data loading for limited bandwidth scenarios

### User Flows for Critical Processes

#### BOI Filing Submission Flow
1. User navigates to BOI Filings section
2. Selects "Create New Filing"
3. Enters Reporting Company Information
   - Validation occurs on completion
   - Sensitive fields marked with appropriate indicators
4. Proceeds to Beneficial Owners section
   - Can add multiple owners
   - Document upload for ID verification
   - Ownership details specification
5. Reviews all information
6. Submits filing or saves as draft
7. Receives confirmation with filing ID
8. Can track status on dashboard

#### Document Upload and Management Flow
1. User navigates to Document Management
2. Selects "Upload New Document"
3. Chooses document type from dropdown
4. Selects entity/owner associated with document
5. Sets document sensitivity level
6. Uploads file (drag-and-drop or file browser)
7. Preview displayed with option to rotate/crop
8. Adds metadata (expiration date, description)
9. Submits and receives encryption confirmation
10. Document appears in relevant sections with appropriate access controls

## 3. MOBILE APPLICATION DESIGN

### Mobile-Specific UI Adaptations
- Single column layout optimized for vertical scrolling
- Bottom navigation bar for primary actions (replaces sidebar)
- Floating action button (FAB) for primary create actions
- Simplified header with dropdown menu
- Swipe gestures for common actions (archive, mark complete)
- Collapsible sections to manage information density
- Mobile-optimized forms with larger input fields
- Sticky call-to-action buttons always visible at bottom of screen

### Native Feature Integration
- **Camera Access**: 
  - Document scanning with automatic edge detection
  - OCR for extracting data from ID documents
  - ID verification using device camera
- **Biometric Authentication**:
  - Fingerprint/Face ID login option
  - Secondary biometric verification for sensitive actions
- **Push Notifications**:
  - Filing status updates
  - Compliance deadline reminders
  - Document approval requests
  - Security alerts
- **Offline Mode**:
  - Form data cached for completion without connectivity
  - Document queue for uploads when connection is restored
- **Calendar Integration**:
  - Add compliance deadlines to device calendar
  - Set reminders for upcoming filings

### Navigation Pattern
- **Primary**: Tab-based bottom navigation with 5 key sections:
  - Dashboard
  - Filings
  - Documents
  - Entities
  - Profile
- **Secondary**: Drawer menu accessed via hamburger icon for less frequent actions:
  - Settings
  - Help & Support
  - About
  - Terms & Policies
  - Logout
- **Tertiary**: In-page navigation via:
  - Breadcrumbs for deep navigation paths
  - Back button in header
  - Swipe gestures between related screens

### Key Screen Mockups Optimized for Mobile

#### Mobile Dashboard
```
+--------------------------------+
| BOI Compliance    [Menu] [👤] |
+--------------------------------+
| Filing Status                  |
| +----------------------------+ |
| | ✅ Completed: 12           | |
| | ⏳ In Progress: 3          | |
| | ⚠️ Action Needed: 1        | |
| +----------------------------+ |
|                                |
| Recent Activity                |
| +----------------------------+ |
| | Today                      | |
| | - ABC Corp filing approved | |
| | - New document uploaded    | |
| |                            | |
| | Yesterday                  | |
| | - XYZ Corp filing submitted| |
| +----------------------------+ |
|                                |
| Upcoming Deadlines             |
| +----------------------------+ |
| | Mar 15 - Annual filing due | |
| | Apr 02 - Document expires  | |
| +----------------------------+ |
|                                |
| [+] (Floating Action Button)   |
+--------------------------------+
| [📊] [📄] [🏢] [📁] [👤]      |
+--------------------------------+
```

#### Mobile BOI Filing Form
```
+--------------------------------+
| < New Filing         [Save]    |
+--------------------------------+
| Step 2 of 3: Beneficial Owners |
|                                |
| [○] [●] [○]                    |
| Company  Owners  Review        |
|                                |
| Beneficial Owner #1            |
| +----------------------------+ |
| | SENSITIVE INFORMATION      | |
| |                            | |
| | Full Name                  | |
| | [John Michael Smith      ] | |
| |                            | |
| | Date of Birth              | |
| | [01/15/1980              ] | |
| |                            | |
| | Address                    | |
| | [123 Main Street         ] | |
| | [Suite 100               ] | |
| | [New York, NY 10001      ] | |
| |                            | |
| | Identification             | |
| | [📷 Take Photo] [📁 Upload] | |
| | ID Type: [Driver's License▼] | |
| |                            | |
| | Ownership Percentage       | |
| | [25                      ]%| |
| +----------------------------+ |
|                                |
| + Add Another Owner            |
|                                |
| [Previous]      [Next]         |
+--------------------------------+
| [📊] [📄] [🏢] [📁] [👤]      |
+--------------------------------+
```

#### Mobile Document View
```
+--------------------------------+
| < Documents                    |
+--------------------------------+
| [🔍 Search documents]          |
|                                |
| Filter: [All Documents      ▼] |
|                                |
| RECENTLY ADDED                 |
| +----------------------------+ |
| | 📄 Articles of Incorporation| |
| | ABC Corporation            | |
| | Added: Today, 2:30 PM      | |
| +----------------------------+ |
|                                |
| +----------------------------+ |
| | 🆔 Passport                | |
| | John Smith                 | |
| | SENSITIVE INFORMATION      | |
| | Added: Yesterday           | |
| +----------------------------+ |
|                                |
| +----------------------------+ |
| | 📄 Operating Agreement     | |
| | XYZ LLC                    | |
| | Added: Mar 12, 2025        | |
| +----------------------------+ |
|                                |
| [+] (Floating Action Button)   |
+--------------------------------+
| [📊] [📄] [🏢] [📁] [👤]      |
+--------------------------------+
```

### Offline Capabilities and Synchronization Approach
- **Data Storage**:
  - AsyncStorage/SQLite for structured data
  - FileSystem API for document caching
  - Encrypted local storage for sensitive information
- **Synchronization Strategy**:
  - Background sync when connectivity restored
  - Delta syncing to minimize data transfer
  - Conflict resolution with server-side timestamps
  - Queue-based approach for failed API calls
- **Offline Actions Supported**:
  - View previously accessed documents
  - Fill out forms and save as drafts
  - Review entity and owner information
  - Capture documents via camera for later upload
- **Sync Indicators**:
  - Visual indicators for offline mode
  - Sync status badges on content
  - Background sync notifications
  - Data freshness timestamps

## 4. SECURITY & COMPLIANCE UI ELEMENTS

### Authentication Screens and Flows

#### Login Screen
```
+--------------------------------+
|                                |
|          [Company Logo]        |
|                                |
| BOI Compliance Platform        |
|                                |
| [Email/Username             ]  |
|                                |
| [Password                   ]  |
|                                |
| [Forgot Password?]  [Login →]  |
|                                |
| [OAuth options if applicable]  |
|                                |
| 🔒 Secure Connection           |
| SOC 2 Type II Compliant        |
+--------------------------------+
```

#### Multi-Factor Authentication
```
+--------------------------------+
|                                |
|          [Company Logo]        |
|                                |
| Verify Your Identity           |
|                                |
| We've sent a verification code |
| to your registered device.     |
|                                |
| [Code Input Fields]            |
| [ ][ ][ ][ ][ ][ ]             |
|                                |
| [Resend Code (30s)]  [Verify] |
|                                |
| [Use Alternative Method ▼]     |
|                                |
| 🔒 Session expires in: 5:00    |
+--------------------------------+
```

#### Session Timeout Warning
```
+--------------------------------+
|                                |
|      ⚠️ Session Expiring       |
|                                |
| Your session will expire in    |
| 2 minutes due to inactivity.   |
|                                |
| Would you like to continue?    |
|                                |
| [Logout Now]    [Stay Logged In]|
|                                |
+--------------------------------+
```

### Permission Visualization

#### Role-Based Access Control Display
```
+--------------------------------+
| User Permissions                |
+--------------------------------+
| John Smith - Administrator     |
|                                |
| Permission Groups:             |
| [✓] User Management            |
| [✓] BOI Filing                 |
| [✓] Document Management        |
| [✓] Entity Management          |
| [✓] System Configuration       |
|                                |
| Data Access Levels:            |
| [■■■■■] Company Data (Full)    |
| [■■■■■] Owner Data (Full)      |
| [■■■■□] Financial Data (View)  |
| [■■■■■] Document Data (Full)   |
|                                |
| [View Audit Log]  [Edit]       |
+--------------------------------+
```

#### Restricted Action Indicator
```
+--------------------------------+
|           🔒                   |
|      Access Restricted         |
|                                |
| You do not have permission to  |
| perform this action.           |
|                                |
| Required permission:           |
| Document Deletion              |
|                                |
| [Request Access]   [Cancel]    |
+--------------------------------+
```

### Audit Log Presentation

#### Activity Timeline
```
+--------------------------------+
| System Activity Log            |
+--------------------------------+
| [Filters] [Date Range] [Export]|
|                                |
| March 15, 2025                 |
| 10:45 AM - John S. (Admin)     |
| → Created new filing for       |
|   ABC Corporation              |
|   IP: 192.168.1.45             |
|                                |
| 09:30 AM - Sarah K. (Compliance)|
| → Approved document upload     |
|   for XYZ LLC                  |
|   IP: 192.168.1.32             |
|                                |
| March 14, 2025                 |
| 03:15 PM - System              |
| → Automatic backup completed   |
|   Success: 342 records         |
|                                |
| 01:20 PM - Mike T. (User)      |
| → Failed login attempt         |
|   IP: 192.168.1.50             |
|   Reason: Invalid credentials  |
|                                |
| [Load More]                    |
+--------------------------------+
```

#### User Session Log
```
+--------------------------------+
| Active Sessions                |
+--------------------------------+
| Current Session                |
| Device: Chrome / Windows       |
| Location: New York, NY         |
| Started: Today, 9:30 AM        |
| Status: Active                 |
| [Terminate]                    |
|                                |
| Other Active Sessions          |
| Device: iOS / iPhone           |
| Location: New York, NY         |
| Started: Today, 8:15 AM        |
| Status: Active                 |
| [Terminate]                    |
|                                |
| Recent Sessions                |
| Device: Safari / Mac           |
| Location: Boston, MA (Unusual) |
| Started: Mar 13, 2025, 7:45 PM |
| Ended: Mar 13, 2025, 8:30 PM   |
| [Report Suspicious]            |
+--------------------------------+
```

### Data Sensitivity Indicators

#### PII Field Markers
```
+--------------------------------+
| Personal Information           |
+--------------------------------+
|                                |
| 🔴 HIGH SENSITIVITY            |
| Social Security Number:        |
| [••••••••••]   [👁️ Show]      |
|                                |
| 🟠 MEDIUM SENSITIVITY          |
| Date of Birth:                 |
| [01/15/1980]                   |
|                                |
| 🔵 STANDARD DATA               |
| Name:                          |
| [John Smith]                   |
|                                |
| ℹ️ Data is encrypted and       |
|    compliant with FinCEN       |
|    requirements                |
+--------------------------------+
```

#### Document Sensitivity Classification
```
+--------------------------------+
| Document Classification        |
+--------------------------------+
|                                |
| Current: 🟠 Medium Sensitivity |
|                                |
| Set Classification Level:      |
|                                |
| ⚪ Public                      |
| Information that can be freely |
| shared.                        |
|                                |
| 🔵 Internal                    |
| For use within the organization|
|                                |
| 🟠 Confidential                |
| Sensitive business information |
|                                |
| 🔴 Restricted                  |
| Critical personal/business data|
| with regulatory implications   |
|                                |
| [Cancel]      [Save]           |
+--------------------------------+
```

## 5. TECHNICAL IMPLEMENTATION RECOMMENDATIONS

### Recommended Frameworks and Libraries

#### Web Application
- **Core Framework**: React (or Angular if preferred)
- **UI Component Libraries**:
  - Material UI or Chakra UI for React
  - Angular Material for Angular
- **Form Management**:
  - Formik or React Hook Form (React)
  - Angular Reactive Forms (Angular)
- **Form Validation**: Yup or Zod
- **State Management**:
  - Redux Toolkit or Zustand (React)
  - NgRx (Angular)
- **API Communication**:
  - React Query or SWR (React)
  - Angular HTTP Client with RxJS (Angular)
- **Authentication**:
  - AWS Amplify Auth for Cognito integration
  - JWT handling utilities
- **Visualization**:
  - Chart.js or D3.js for graphs
  - react-flow or vis.js for relationship visualizations
- **Security**:
  - crypto-js for client-side encryption
  - secure-ls for encrypted local storage

#### Mobile Application
- **Core Framework**: React Native
- **UI Component Library**: React Native Paper
- **Navigation**: React Navigation
- **State Management**: Redux Toolkit or Zustand
- **Form Management**: Formik with Yup
- **API Communication**: React Query
- **Authentication**: AWS Amplify Auth
- **Device Features**:
  - react-native-camera for document scanning
  - react-native-biometrics for fingerprint/Face ID
  - react-native-fs for file system access
  - react-native-push-notification for alerts
- **Offline Support**:
  - WatermelonDB or SQLite for local database
  - @react-native-async-storage/async-storage

### State Management Approach

#### Layered State Architecture
```
Global Application State (Redux/Zustand/NgRx)
├── Authentication State
│   ├── User profile
│   ├── Permissions
│   └── Session information
├── UI State
│   ├── Theme preferences
│   ├── Layout settings
│   └── Notification state
├── Entity Data State
│   ├── Companies
│   ├── Beneficial owners
│   └── Documents metadata
└── Form State (Local)
    ├── Current form values
    ├── Validation state
    └── Submission state
```

#### State Management Strategy
- **Server State**: Use React Query/SWR (React) or RxJS (Angular) for:
  - Data fetching with caching
  - Automatic refetching
  - Pagination handling
  - Optimistic updates
- **Client State**: Use Redux/Zustand/NgRx for:
  - Authentication state
  - Global UI state
  - Cross-component shared state
- **Local State**: Use component state/hooks for:
  - UI interactions
  - Form state during editing
  - Component-specific toggling

### Performance Optimization Strategies

#### Loading Performance
- Code splitting based on routes
- Lazy loading of heavy components
- Tree shaking to eliminate unused code
- Efficient bundling with Webpack/Rollup
- Asset optimization (images, fonts)
- Prefetching critical resources

#### Runtime Performance
- Memoization of expensive calculations (useMemo, useCallback)
- Virtualized lists for long scrollable content
- Debouncing/throttling for frequent events
- Strategic re-rendering prevention
- Web workers for heavy calculations
- Skeleton screens during data loading

#### Mobile-Specific Optimizations
- Hermes JavaScript engine for React Native
- Image resizing before upload
- Progressive loading of high-resolution assets
- Minimize bridge crossing in React Native
- Native modules for performance-critical features

### Shared Code Opportunities Between Web and Mobile

#### Architecture for Code Sharing
```
/src
├── /core               # Shared business logic
│   ├── /api            # API interfaces
│   ├── /models         # Data models
│   ├── /utils          # Shared utilities
│   └── /validation     # Validation rules
├── /ui-components      # Shared component patterns
│   ├── /web            # Web implementations
│   └── /mobile         # Mobile implementations
├── /features           # Feature modules
│   ├── /auth           # Authentication logic
│   ├── /filing         # Filing business logic
│   └── /documents      # Document handling
├── /web                # Web-specific code
└── /mobile             # Mobile-specific code
```

#### Specific Sharing Strategies
- **Business Logic**: 
  - Use TypeScript for shared models and interfaces
  - Create platform-agnostic services for core functionality
  - Share validation rules and form schemas

- **UI Component Patterns**:
  - Define common component interfaces
  - Implement platform-specific versions with same API
  - Share styling constants and theming

- **State Management**:
  - Share Redux/Zustand stores and reducers
  - Use adapters for platform-specific persistence

- **API Communication**:
  - Share API client configuration
  - Use same data transformation and normalization

- **Testing**:
  - Share test fixtures and mock data
  - Unified testing strategy across platforms

This comprehensive front-end design provides a solid foundation for building a secure, accessible, and user-friendly BOI Compliance Management Platform across both web and mobile devices, with careful attention to security, compliance, and user experience.