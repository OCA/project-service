/** @odoo-module */

import {ProjectRightSidePanel} from "@project/components/project_right_side_panel/project_right_side_panel";
import {patch} from "@web/core/utils/patch";

patch(ProjectRightSidePanel.prototype, {
    // ---------------------------------------------------------------------
    // Handlers
    // ---------------------------------------------------------------------

    /**
     * @private
     * @param {Object} params
     */
    async onReimbursementItemActionClick(params) {
        const action = await this.actionService.loadAction(params.name, this.context);
        this.actionService.doAction({
            ...action,
            res_id: params.resId,
            views: [[false, "form"]],
        });
    },
});
