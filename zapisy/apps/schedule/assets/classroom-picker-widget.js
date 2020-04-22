import Vue from "vue";
import ClassroomPicker from "./components/ClassroomPicker.vue";

let schedule_classroom_picker_app = new Vue({
  el: "#classroom-picker",
  components: {
    ClassroomPicker,
  },
  render: function (h) {
    return h(ClassroomPicker);
  },
});
