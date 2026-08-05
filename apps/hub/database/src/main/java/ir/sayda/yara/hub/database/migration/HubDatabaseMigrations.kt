package ir.sayda.yara.hub.database.migration

import androidx.room.migration.Migration
import androidx.sqlite.db.SupportSQLiteDatabase

val MIGRATION_1_2 = object : Migration(1, 2) {
    override fun migrate(db: SupportSQLiteDatabase) {
        db.execSQL(
            """
            ALTER TABLE outbox_entry ADD COLUMN priority INTEGER NOT NULL DEFAULT 0
            """.trimIndent(),
        )
        db.execSQL(
            """
            ALTER TABLE outbox_entry ADD COLUMN updated_at_epoch_millis INTEGER NOT NULL DEFAULT 0
            """.trimIndent(),
        )
        db.execSQL(
            """
            ALTER TABLE outbox_entry ADD COLUMN last_error TEXT
            """.trimIndent(),
        )
        db.execSQL(
            """
            UPDATE outbox_entry SET updated_at_epoch_millis = created_at_epoch_millis
            WHERE updated_at_epoch_millis = 0
            """.trimIndent(),
        )

        db.execSQL(
            """
            ALTER TABLE pending_evidence ADD COLUMN correlation_id TEXT NOT NULL DEFAULT ''
            """.trimIndent(),
        )
        db.execSQL(
            """
            ALTER TABLE pending_evidence ADD COLUMN idempotency_key TEXT NOT NULL DEFAULT ''
            """.trimIndent(),
        )
        db.execSQL(
            """
            ALTER TABLE pending_evidence ADD COLUMN retry_count INTEGER NOT NULL DEFAULT 0
            """.trimIndent(),
        )
        db.execSQL(
            """
            ALTER TABLE pending_evidence ADD COLUMN updated_at_epoch_millis INTEGER NOT NULL DEFAULT 0
            """.trimIndent(),
        )
        db.execSQL(
            """
            ALTER TABLE pending_evidence ADD COLUMN last_error TEXT
            """.trimIndent(),
        )
        db.execSQL(
            """
            UPDATE pending_evidence
            SET updated_at_epoch_millis = created_at_epoch_millis,
                idempotency_key = id
            WHERE updated_at_epoch_millis = 0
            """.trimIndent(),
        )
        db.execSQL("CREATE INDEX IF NOT EXISTS index_outbox_entry_priority ON outbox_entry(priority)")
        db.execSQL("CREATE INDEX IF NOT EXISTS index_pending_evidence_correlation_id ON pending_evidence(correlation_id)")
        db.execSQL(
            """
            CREATE UNIQUE INDEX IF NOT EXISTS index_pending_evidence_idempotency_key
            ON pending_evidence(idempotency_key)
            """.trimIndent(),
        )
    }
}
