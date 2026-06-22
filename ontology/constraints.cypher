// --- Uniqueness constraints (also create backing indexes) ---
CREATE CONSTRAINT plant_id    IF NOT EXISTS FOR (n:Plant)          REQUIRE n.id IS UNIQUE;
CREATE CONSTRAINT asset_tag   IF NOT EXISTS FOR (n:Asset)          REQUIRE (n.plant_id, n.tag) IS UNIQUE;
CREATE CONSTRAINT proc_id     IF NOT EXISTS FOR (n:Procedure)      REQUIRE n.id IS UNIQUE;
CREATE CONSTRAINT doc_id      IF NOT EXISTS FOR (n:Document)       REQUIRE n.id IS UNIQUE;
CREATE CONSTRAINT chunk_id    IF NOT EXISTS FOR (n:Chunk)          REQUIRE n.id IS UNIQUE;
CREATE CONSTRAINT reg_id      IF NOT EXISTS FOR (n:Regulation)     REQUIRE n.id IS UNIQUE;
CREATE CONSTRAINT incident_id IF NOT EXISTS FOR (n:Incident)       REQUIRE n.id IS UNIQUE;
CREATE CONSTRAINT fmode_id    IF NOT EXISTS FOR (n:FailureMode)    REQUIRE n.id IS UNIQUE;
CREATE CONSTRAINT meas_id     IF NOT EXISTS FOR (n:Measurement)    REQUIRE n.id IS UNIQUE;
CREATE CONSTRAINT person_id   IF NOT EXISTS FOR (n:Person)         REQUIRE n.id IS UNIQUE;
CREATE CONSTRAINT tribal_id   IF NOT EXISTS FOR (n:TribalNote)     REQUIRE n.id IS UNIQUE;
CREATE CONSTRAINT eqclass_id  IF NOT EXISTS FOR (n:EquipmentClass) REQUIRE n.id IS UNIQUE;

// --- Lookup indexes ---
CREATE INDEX asset_name  IF NOT EXISTS FOR (n:Asset)       ON (n.name);
CREATE INDEX proc_name   IF NOT EXISTS FOR (n:Procedure)   ON (n.name);
CREATE INDEX meas_param  IF NOT EXISTS FOR (n:Measurement) ON (n.parameter);
CREATE INDEX incident_t  IF NOT EXISTS FOR (n:Incident)    ON (n.occurred_at);

// --- Full-text index for name resolution in queries ---
CREATE FULLTEXT INDEX entity_fulltext IF NOT EXISTS
    FOR (n:Asset|Procedure|FailureMode|Regulation|TribalNote)
    ON EACH [n.name, n.aliases];
