<script lang="ts">
import Vue from "vue";
import Component from "vue-class-component";

import TextFilter from "@/enrollment/timetable/assets/components/filters/TextFilter.vue";
// import LabelsFilter from "@/enrollment/timetable/assets/components/filters/LabelsFilter.vue";
import SelectFilter from "@/enrollment/timetable/assets/components/filters/SelectFilter.vue";
import CheckFilter from "@/enrollment/timetable/assets/components/filters/CheckFilter.vue";
export default Vue.extend({
  components: {
    TextFilter,
    SelectFilter,
    CheckFilter
  },
  data: function() {
    return {
      allEffects: {},
      allTags: {},
      allOwners: [] as [number, string][],
      allSemesters: [] as [string, string][],
      allStatuses: [] as [string, string][],
      allTypes: {},

      // The filters are going to be collapsed by default.
      collapsed: true
    };
  },
  created: function() {
    this.allTypes = [
      ["ISIM", "ISIM"],
      ["inż", "Inżynierska"],
      ["mgr", "Magisterska"],
      ["lic", "Licencajcka"],
      ["lic+inż", "Lic+inż"],
      ["lic+inż+isim", "Lic+inż+isim"]
    ];
  }
});
</script>

<template>
  <div class="card bg-light">
    <div class="card-body" v-bind:class="{ collapsed: collapsed }">
      <TextFilter filterKey="name-filter" property="name" placeholder="Nazwa pracy dyplomowej" />

      <SelectFilter
        filterKey="type-filter"
        property="thesisType"
        :options="allTypes"
        placeholder="Rodzaj przedmiotu"
      />

      <CheckFilter
        filterKey="available-filter"
        property="showAvailable"
        label="Pokaż tylko niezarezerwowane prace"
      />
    </div>
    <div class="card-footer p-1 text-center">
      <a href="#" @click.prevent="collapsed = !collapsed">zwiń / rozwiń</a>
    </div>
  </div>
</template>

<style lang="scss" scoped>
.collapsed {
  overflow-y: hidden;
  height: 120px;

  // Blurs over the bottom of filter card.
  &:after {
    position: absolute;
    display: block;
    // Height of the card footer.
    bottom: 28px;
    left: 0;
    height: 50%;
    width: 100%;
    content: "";
    // Bootstrap light colour.
    background: linear-gradient(
      to top,
      rgba(248, 249, 250, 1) 0%,
      rgba(248, 249, 250, 0) 100%
    );
    pointer-events: none; /* so the text is still selectable */
  }
}
</style>