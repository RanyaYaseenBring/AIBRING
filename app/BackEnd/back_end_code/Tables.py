SCHEMA = {

    "etl.APITokens": {
        "description": "API tokens, authenticatie, client credentials en omgevingen",
        "columns": [
            "EnvironmentType",
            "EnvironmentCode",
            "Token",
            "State",
            "Description",
            "API_Token",
            "CreatedAt",
            "UpdatedAt",
            "client_id",
            "client_secret"
        ]
    },

    "etl.Data_processor": {
        "description": "ETL data verwerking, JSON payloads en bronbestanden",
        "columns": [
            "id",
            "table_target",
            "payload",
            "insert_date",
            "source_sys",
            "json_path"
        ]
    },

    "etl.EndpointConfig": {
        "description": "ETL endpoint configuratie, synchronisaties, query instellingen en imports",
        "columns": [
            "Id",
            "SqlProfile",
            "EndpointName",
            "UniqueIdentifier",
            "IsEnabled",
            "UseDefaultParams",
            "SchemaProbeParamsJson",
            "BaseQueryParamsJson",
            "Take",
            "ProcessQueueNow",
            "EnvironmentCode",
            "EnvironmentType",
            "SortOrder",
            "CreatedAt",
            "UpdatedAt",
            "UniqueKeyJson",
            "DefaultJsonPath",
            "System",
            "Frequency",
            "OracleQuery"
        ]
    },

    "_logs.EtRunLog": {
        "description": "ETL runs, endpoint uitvoeringen, fouten, waarschuwingen en logging gebeurtenissen",
        "columns": [
            "id",
            "profile",
            "endpoint",
            "environment",
            "event_time",
            "level",
            "message",
            "details"
        ]
    },

    "_logs.ProcessingLog": {
        "description": "Verwerking van ETL imports, statussen, fouten en verwerkte records",
        "columns": [
            "id",
            "data_processor_id",
            "table_target",
            "status",
            "start_time",
            "end_time",
            "rows_inserted",
            "column_count",
            "error_message",
            "logged_at"
        ]
    },

    "afas.Bring_Activakaart": {
        "description": "Activa, vaste activa, afschrijvingen, boekwaarden en financiële activa administratie",
        "columns": [
            "Nummer_journaalpost",
            "Activacode",
            "Naam_actief",
            "Grootboekrekening",
            "TypeRekeningNL",
            "Boekjaar_financieel",
            "Periode_financieel",
            "Bedrag",
            "Periode_activa",
            "Boekjaar_activa",
            "Type_item",
            "Afschrijving_initieel",
            "Boekwinst_vorig_actief",
            "Boekwinst_verlies",
            "Boekwaarde"
        ]
    },

    "afas.Bring_Debtor_Invoices": {
        "description": "Debiteurfacturen, openstaande facturen, vervaldatums, saldo's en klantfacturatie",
        "columns": [
            "UnitId",
            "DebtorId",
            "InvoiceNr",
            "NookPieceDate",
            "ExpDate",
            "CurrencyId",
            "AmtInvoice",
            "AmtInvoiceCurr",
            "Balance",
            "BalanceCurr",
            "Description",
            "Datum_gewijzigd",
            "Gewijzigd_door",
            "Omschrijving"
        ]
    },

   "afas.Bring_Employees": {
    "description": """
HOOFDTABEL VOOR MEDEWERKERS EN PERSONEEL.

Gebruik deze tabel voor:
- medewerkers
- personeel
- werknemers
- personen
- persoonsgegevens
- contactgegevens
- telefoonnummer
- mobiel nummer
- email adres
- geboortedatum
- leeftijd
- functie
- afdeling
- contractinformatie

Gebruik deze tabel voor adresgegevens van medewerkers:
- adres
- straat
- huisnummer
- toevoeging
- postcode
- woonplaats
- land

BELANGRIJK:
Wanneer een vraag over een persoon, medewerker of werknemer gaat,
gebruik deze tabel als eerste keuze.

Adresgegevens bestaan uit:
Street
HouseNumber
AddNumber
ZIPCode
City
Country
""",
    "columns": [
        "EmployeeId",
        "PersonId",
        "EmployerId",
        "BSN",
        "BirthName",
        "Initials",
        "PrefixBirthName",
        "DateOfBirth",
        "Gender",
        "MaritalStatus",
        "PrefixPartner",
        "BirthNamePartner",
        "NameUse",
        "Mobile",
        "Phone",
        "Street",
        "HouseNumber",
        "AddNumber",
        "ZIPCode",
        "City",
        "Country",
        "EmploymentStart",
        "EmploymentEnd",
        "HourPerWeek",
        "EmploymentType",
        "EmploymentTypeDesc",
        "FTE",
        "OrgUnit",
        "OrgUnitDesc",
        "FunctionId",
        "FunctionDesc",
        "DateDeceased",
        "Mail",
        "FirstName",
        "Indienst_arbeidsverhouding"
    ]
},

    "afas.Bring_FinancieleMutaties_ESJ": {
        "description": "Financiële mutaties, grootboekboekingen, debiteuren, crediteuren, projecten, journaalposten en financiële administratie",
        "columns": [
            "Naam_administratie",
            "UnitId",
            "Administratie",
            "EntryDate",
            "AccountNo",
            "Grootboekrekeningnr",
            "AmtDebit",
            "AmtCredit",
            "Saldo",
            "Valuta",
            "Koers",
            "Valutabedrag_debet",
            "Valutabedrag_credit",
            "Description",
            "Bron_journaalpost",
            "EntryNo",
            "SeqNo",
            "Volgnummer_journaalpost",
            "Year",
            "Period",
            "VoucherDate",
            "InvoiceId",
            "Code_dagboek",
            "JournalId",
            "Dagboekomschrijving",
            "VoucherNo",
            "Nummer_verplichting",
            "Kenmerk_rekening",
            "Type_rekening_nummer_debiteur_crediteur",
            "Debiteur_crediteur",
            "Subrekening_crediteur",
            "Subrekening_debiteur",
            "Code_verbijzonderingsas_1",
            "Code_verbijzonderingsas_2",
            "Project",
            "ProjectOmschrijving",
            "Type_projectboeking",
            "Toegevoegd_door",
            "Datum_toegevoegd",
            "Gewijzigd_door",
            "Datum_gewijzigd",
            "VatCode",
            "Transitorische_post",
            "Admin_rek_courantboeking",
            "Status_wijziging",
            "DebCredNaam",
            "Verzamelen_op",
            "Hoofdverdichting",
            "Subverdichting",
            "Type_grootboekrekening",
            "Omschrijving",
            "Debiteur_crediteur_2"
        ]
    },

    "afas.Bring_KnOrganisation": {
        "description": "Organisaties, klanten, leveranciers, contactgegevens, administratie en accountmanagement",
        "columns": [
            "BcCo",
            "Type",
            "SearchName",
            "Name",
            "Land",
            "TelWork",
            "MailWork",
            "Homepage",
            "Note",
            "ChOfCommNr",
            "Straat",
            "Huisnummer",
            "toev_huisnr",
            "Postcode",
            "Woonplaats",
            "Accountmanager",
            "Debiteur",
            "Crediteur",
            "Administratie",
            "Klant_productgroepen",
            "Bron",
            "Debiteurnummer"
        ]
    },

    "afas.Bring_LeaveTypes": {
        "description": "Verlofsoorten, verlofcodes en omschrijvingen van verloftypes",
        "columns": [
            "Leavetype",
            "LeaveTypeDesc"
        ]
    },
"afas.Bring_Medewerker_Contract": {
    "description": """
Contractgegevens, dienstverbanden, werkgevers, CAO, arbeidsvoorwaarden en contracthistorie van medewerkers.

BELANGRIJK:
De kolom Medewerker is GEEN naam.
Medewerker verwijst naar afas.Bring_Employees.EmployeeId.

Gebruik bij vragen met een persoonsnaam altijd een JOIN met afas.Bring_Employees.

RELATIE:
afas.Bring_Medewerker_Contract.Medewerker = afas.Bring_Employees.EmployeeId
""",
    "columns": [
        "Medewerker",
        "Volgnummer_dienstverband",
        "Begindatum_contract",
        "Einddatum_contract",
        "Werkgever",
        "Cao",
        "Arbeidsvoorwaarde_code",
        "Dienstbetrekking",
        "Datum_in_dienst",
        "Datum_uit_dienst",
        "Type_contract",
        "Einde_proeftijd_per",
        "Laatste_werkdag",
        "Soort_medewerker",
        "Onbepaalde_tijd",
        "Schriftelijke_arbeidsovereenkomst",
        "Aangemaakt_op",
        "Toegevoegd_door",
        "Gewijzigd_op",
        "Gewijzigd_door"
    ]
},

    "afas.Bring_Medewerker_Functie": {
    "description": "Functies, functiehistorie, organisatorische eenheden, kostenplaatsen en functiewijzigingen van medewerkers",
    "columns": [
        "Medewerker",
        "Volgnummer_dienstverband",
        "Begindatum_contract",
        "Einddatum_contract",
        "Werkgever",
        "Cao",
        "Arbeidsvoorwaarde_code",
        "Dienstbetrekking",
        "Datum_in_dienst",
        "Datum_uit_dienst",
        "Type_contract",
        "Einde_proeftijd_per",
        "Laatste_werkdag",
        "Onbepaalde_tijd",
        "Schriftelijke_arbeidsovereenkomst",
        "Aangemaakt_op",
        "Toegevoegd_door",
        "Gewijzigd_op",
        "Gewijzigd_door"
    ]
},

"afas.Bring_VasteActiva": {
    "description": "Vaste activa, aanschafwaarden, afschrijvingen, restwaardes en activa-administratie",
    "columns": [
        "Administratie",
        "Administratie_3",
        "Activacode",
        "VolgNr_Comm",
        "VolgNr_Fisc",
        "Vaste_activagroep",
        "Omschrijving",
        "Status_actief",
        "Naam_actief",
        "Aanschafdatum",
        "Aanschafwaarde",
        "Additionele_kosten",
        "Begindatum_afschrijving_comm",
        "Einddatum_afschrijving_comm",
        "Restwaarde_comm",
        "Afschrijvingstermijn_comm",
        "Begindatum_afschrijving_fisc",
        "Einddatum_afschrijving_fisc",
        "Restwaarde_fisc",
        "Afschrijvingstermijn_fisc"
    ]
},
    
"afas.Bring_Verzuim": {
    "description": """
BELANGRIJKE REGELS VOOR afas.Bring_Verzuim

Aanwezigheid bevat waarden zoals:
0.0
57.5
82.5
100.0

Interpretatie:
- Aanwezigheid > 0 = aanwezig
- Aanwezigheid = 0 = afwezig

Gebruik altijd:

CAST(Aanwezigheid AS FLOAT)

Voorbeelden:

Vraag:
Welke medewerkers zijn aanwezig?

SQL:
SELECT TOP 100
    Naam,
    Aanwezigheid
FROM afas.Bring_Verzuim
WHERE CAST(Aanwezigheid AS FLOAT) > 0

Vraag:
Welke medewerkers zijn afwezig?

SQL:
SELECT TOP 100
    Naam,
    Aanwezigheid
FROM afas.Bring_Verzuim
WHERE CAST(Aanwezigheid AS FLOAT) = 0
""",
    "columns": [
        "GUID",
        "Medewerker",
        "Naam",
        "Aanwezigheid",
        "Aanwezigheid_AT",
        "Omschrijving",
        "Gewijzigd_op",
        "StartDatum",
        "Einddatum",
        "Werkgever",
        "NaamVervanger"
    ]
},

"afas.Bring_workflow_log": {
    "description": "Workflow acties, taken, gebruikersacties, doelgebruikers en workflow historie",
    "columns": [
        "end_date",
        "user_description",
        "action_description",
        "task_description",
        "duration",
        "line_id",
        "subject_id",
        "user",
        "target_user",
        "target_user_description",
        "user_person_id",
        "target_user_person_id",
        "user_image_id",
        "target_user_image_id"
    ]
},

"afas.Profit_Debtor": {
    "description": "Debiteuren, klanten, betaalgegevens, kredietlimieten en facturatie-informatie",
    "columns": [
        "DebtorId",
        "DebtorName",
        "BcCo",
        "SearchName",
        "AdressLine1",
        "AdressLine3",
        "AdressLine4",
        "TelNr",
        "Email",
        "IBAN",
        "VatNr",
        "ChOfCommNr",
        "CollectAccount",
        "PayCon",
        "VatDuty",
        "Blocked",
        "CreditLimit",
        "CurrencyId",
        "AutoPayment",
        "CreateDate",
        "ModifiedDate"
    ]
},

"afas.Profit_Users": {
    "description": """
Gebruikersaccounts en systeemtoegang.

Gebruik ALLEEN voor:
- UserId
- UPN
- login
- account
- InSite
- OutSite
- Connector
- geblokkeerde gebruikers

Gebruik NOOIT voor:
- BSN
- telefoon
- mobiel
- email van medewerkers
- adres
- woonplaats
- geboortedatum
- medewerkergegevens
"""},

"afas.Profit_Employers": {
    "description": "Werkgevers, organisaties, organisatorische eenheden en financiële dimensies",
    "columns": [
        "EmployerId",
        "Name",
        "OrganisationId",
        "AddressLine1",
        "AddressLine3",
        "AddressLine4",
        "DimAx1",
        "DimAx2",
        "DimAx3",
        "DimAx4",
        "DimAx5",
        "UnitId"
    ]
},

"afas.Profit_Journals": {
    "description": "Dagboeken, journaaltypen, financiële journalen en blokkeringen",
    "columns": [
        "UnitId",
        "JournalId",
        "Description",
        "JournalType",
        "Blocked"
    ]
},

"afas.Profit_LeaveBalance": {
    "description": "Verlofsaldo, vakantiedagen, opgenomen verlof en resterende verlofrechten van medewerkers",
    "columns": [
        "EmployeeId",
        "EmployerId",
        "DvId",
        "Leavetype",
        "Year",
        "Period",
        "Entitlement",
        "ExtraEntitlement",
        "StartBalance",
        "Taken",
        "Balance"
    ]
},

"afas.Profit_Leaves": {
    "description": "Verlofregistraties, verlofaanvragen, verlofuren, verlofperiodes en verlofredenen van medewerkers",
    "columns": [
        "LeaveId",
        "EmployeeId",
        "Name",
        "BSN",
        "Export",
        "Hours",
        "StartDate",
        "EndDate",
        "DvId",
        "ModifiedDate",
        "LeaveCode",
        "LeaveDescr",
        "ReasonCode",
        "ReasonDescr"
    ]
},

"afas.Profit_UserGroups": {
    "description": "Gebruikersgroepen, groepslidmaatschappen en koppelingen tussen gebruikers en groepen",
    "columns": [
        "GroupId",
        "Decription",
        "UserId"
    ]
},


"dbo.Tally": {
    "description": "Technische hulpartabel met nummerreeksen voor tellingen, loops en datageneratie",
    "columns": [
        "n"
    ]
},

"LSP_NL.bcnl_bree_searchnames": {
    "description": "Logistieke zoekgegevens voor plaatsen, postcodes, landen en zoeknamen",
    "columns": [
        "zoek",
        "postka",
        "plaats",
        "land"
    ]
},

"LSP_NL.bcnl_edirefs": {
    "description": "EDI referenties, logistieke dossiernummers en koppelingen tussen EDI en PEMR gegevens",
    "columns": [
        "dosvlg",
        "tsEDIr",
        "pemr"
    ]
},

"LSP_NL.peppol_lijn12": {
    "description": "Peppol logistieke gegevens, relatienummers, dossiernummers, rolnummers en PEMR koppelingen",
    "columns": [
        "zoek",
        "relnr",
        "dosvlg",
        "tsroln",
        "pemr",
        "ID"
    ]
},

}