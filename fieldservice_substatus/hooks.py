import logging

_logger = logging.getLogger(__name__)


def post_init_hook(env):
    default_sub_stage = env.ref(
        'fieldservice_substatus.fsm_stage_status_default',
        raise_if_not_found=False,
    )
    if not default_sub_stage:
        _logger.warning("fieldservice_substatus: default sub-stage not found, skipping")
        return
    stages = env['fsm.stage'].search([('sub_stage_id', '=', False)])
    if stages:
        stages.write({'sub_stage_id': default_sub_stage.id})
        _logger.info("fieldservice_substatus: applied default sub_stage_id to %d stages", len(stages))
