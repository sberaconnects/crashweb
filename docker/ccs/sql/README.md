# Datenbank-Schema: coredumps

## ER-Diagramm

```mermaid
erDiagram
    cla_sw_rev {
        int clb_id PK
        varchar clb_rev
        int clb_type
    }

    cla_devices {
        int cla_id PK
        varchar cla_ip_addr
        varchar cla_eqm_label
        int cla_upgrade_method
        int cla_eqm_type
        varchar cla_eqm_name
    }

    cla_core {
        int clc_id PK
        int clc_sw_rev FK
        int clc_device FK
        varchar clc_core_name
        varchar clc_core_binary
        int clc_core_signal
        varchar clc_core_file
        datetime clc_date
        varchar clc_bt_csum
    }

    cla_backtrace {
        int cle_id PK
        int cle_core FK
        int cle_line_no
        varchar cle_line
    }

    cla_journal {
        int cld_id PK
        int cld_core FK
        int cld_line_no
        varchar cld_line
        datetime cld_date
    }

    cla_sw_rev ||--o{ cla_core : "clc_sw_rev"
    cla_devices ||--o{ cla_core : "clc_device"
    cla_core ||--o{ cla_backtrace : "cle_core"
    cla_core ||--o{ cla_journal : "cld_core"
```

## Tabellen

| Tabelle | Beschreibung |
|---|---|
| `cla_sw_rev` | Software-Revisionen (Version und Typ) |
| `cla_devices` | Geraete (IP-Adresse, Label, Typ, Name) |
| `cla_core` | Coredump-Eintraege, verknuepft mit Software-Revision und Geraet |
| `cla_backtrace` | Backtrace-Zeilen zu einem Coredump |
| `cla_journal` | Journal-Eintraege zu einem Coredump |

## Beziehungen

- Ein **Geraet** (`cla_devices`) kann mehrere **Coredumps** (`cla_core`) haben.
- Eine **Software-Revision** (`cla_sw_rev`) kann in mehreren **Coredumps** referenziert werden.
- Ein **Coredump** (`cla_core`) kann mehrere **Backtrace-Zeilen** (`cla_backtrace`) und **Journal-Eintraege** (`cla_journal`) haben.

## Benutzer

| Benutzer | Berechtigungen |
|---|---|
| `ccs` | Alle Rechte auf `coredumps.*` |
| `apache` | Nur Leserechte (`SELECT`) auf `coredumps.*` |