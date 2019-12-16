import Vue from "vue";
import Vuex from "vuex";

import theses from "./theses";
import filters from "./filters";

Vue.use(Vuex);

export default new Vuex.Store({
  modules: {
    theses,
    filters
  }
});
