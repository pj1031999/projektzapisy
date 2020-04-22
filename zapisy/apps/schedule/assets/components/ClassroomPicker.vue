<script lang="ts">
import Vue from "vue";
import Component from "vue-class-component";
import ClassroomField from "./ClassroomField.vue";

@Component({
  components: {
    ClassroomField
  }
})
export default class ClassroomPicker extends Vue {}
</script>

<template>
  <div>
    <h3>Filtruj sale</h3>
    <ClassroomField label="Sala 4" capacity="40" type="Sala ćwiczeniowa" />
    <ClassroomField label="Sala 119" capacity="85" type="Sala wykładowa" />
  </div>
</template>