odoo.define('sercop_ai.AiQuotationRefresh', function (require) {
    'use strict';

    var AbstractField = require('web.AbstractField');
    var field_registry = require('web.field_registry');

    var AiStateDisplay = AbstractField.extend({
        supportedFieldTypes: ['integer'],
        init: function () {
            this._interval = null;
            this._retries = 0;
            this._super.apply(this, arguments);
        },
        _render: function () {
            var state = this.recordData.state;
            if (state === 'processing') {
                this._startPolling();
            } else {
                this._stopPolling();
            }
        },
        _startPolling: function () {
            if (this._interval) return;
            var self = this;
            this._retries = 0;
            this._interval = setInterval(function () {
                self._retries++;
                self.trigger_up('reload_view');
                if (self._retries >= 60) {
                    self._stopPolling();
                }
            }, 10000);
        },
        _stopPolling: function () {
            if (this._interval) {
                clearInterval(this._interval);
                this._interval = null;
            }
        },
        destroy: function () {
            this._stopPolling();
            this._super.apply(this, arguments);
        },
    });

    field_registry.add('ai_state_display', AiStateDisplay);

    return AiStateDisplay;
});
