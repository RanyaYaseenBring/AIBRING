 TABLE_GROUPS = {

    "employees": [
        "afas.Bring_Employees",
        "afas.Profit_Employees",
        "afas.Profit_Users",
        "afas.Profit_UserGroups"
    ],

    "employee_details": [
        "afas.Bring_Medewerker_Functie",
        "afas.Bring_Medewerker_Contract",
        "afas.Bring_Medewerker_Salaris",
        "afas.Bring_Verzuim",
        "afas.Bring_LeaveTypes",
        "afas.Profit_LeaveBalance"
    ],

    "finance": [
        "afas.Bring_FinancieleMutaties_ESJ",
        "afas.Bring_Debtor_Invoices",
        "afas.Profit_Debtor",
        "afas.Profit_Journals"
    ],

    "organization": [
        "afas.Bring_KNOrganisation"
    ],

    "workflow": [
        "afas.Bring_workflow_log"
    ],

    "logs": [
        "_logs.ProcesssingLog",
        "_logs.EtlRunLog"
    ],

    "system": [
        "_etl.APITokens",
        "_etl.Data_processor",
        "_etl.EndpointConfig"
    ],

    "LSP": [
        "dbo.Tally",
        "LSP_NL.bcnl_edirefs",
        "LSP_NL.peppol_lijn12"
    ]
}