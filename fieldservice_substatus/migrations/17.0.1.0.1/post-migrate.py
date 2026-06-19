import logging

_logger = logging.getLogger(__name__)


def migrate(cr, version):
    cr.execute("""
        UPDATE fsm_stage s
        SET sub_stage_id = (
            SELECT id FROM fsm_stage_status WHERE name = 'Default' LIMIT 1
        )
        WHERE s.sub_stage_id IS NULL
          AND EXISTS (SELECT 1 FROM fsm_stage_status WHERE name = 'Default')
    """)
    _logger.info("fieldservice_substatus migrate: set default sub_stage_id on %d stages", cr.rowcount)
