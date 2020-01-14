import { property } from "lodash";

import { ThesisInfo } from "./theses";

interface State {
  property: string;
  order: boolean;
}
const state: State = {
  property: "",
  order: false
};

const getters = {
  // compare compares two theses based on current sorter
  compare: (state: State) => (
    a: ThesisInfo,
    b: ThesisInfo
  ) => {
    let propGetter = property(state.property) as (
      c: ThesisInfo
    ) => string;
    return state.order
      ? propGetter(a).localeCompare(propGetter(b))
      : propGetter(b).localeCompare(propGetter(a));
  },
  isEmpty: (state: State) => {
    return state.property == "";
  },
  getProperty: (state: State) => {
    return state.property;
  }
};

const mutations = {
  // changeSorting can be also used to update filter data.
  changeSorting(
    state: State,
    { k, f }: { k: string; f: boolean }
  ) {
    state.property = k;
    state.order = f;
  }
};

const actions = {};

export default {
  namespaced: true,
  state,
  getters,
  actions,
  mutations
};
