import Vue from "vue";

import ThesisFilter from "./components/ThesisFilter.vue";

let theses_filter_app = new Vue({
    el: "#thesis-filter",
    components: {
        ThesisFilter
    },
    render: function (h) {
        return h(ThesisFilter);
    }
});
