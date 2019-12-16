<script lang="ts">
import Vue from "vue";
import Component from "vue-class-component";

import TextFilter from "./filters/TextFilter.vue";
import SelectFilter from "./filters/SelectFilter.vue";
import CheckFilter from "./filters/CheckFilter.vue";

export default Vue.extend({
  components: {
    TextFilter,
    SelectFilter,
    CheckFilter
  },
  data: function() {
    return {
      allKinds: {}
    };
  },
  created: function() {
    this.allKinds = [
      ["mgr", "Magisterska"],
      ["inż", "Inżynierska"],
      ["lic", "Licencjacka"],
      ["isim", "ISIM"],
      ["lic+inż", "Licencjat+inżynierska"],
      ["lic+inż+isim", "Licencjat+inżynierska+ISIM"]
    ];
  }
});
</script>

<template>
  <div class="card bg-light">
    <div class="card-body">
      <div class="row">
        <div class="col-md">
          <TextFilter
            filterKey="name-filter"
            property="title"
            placeholder="Nazwa pracy dyplomowej"
          />
        </div>
        <div class="col-md">
          <SelectFilter
            filterKey="type-filter"
            property="kind"
            :options="allKinds"
            placeholder="Typ pracy dyplomowej"
          />
        </div>
      </div>
      <div class="row">
        <div class="col-md">
          <CheckFilter
            filterKey="available-filter"
            property="is_available"
            label="Pokaż tylko dostępne prace"
          />
        </div>
      </div>
    </div>
  </div>
</template>

<style lang="scss" scoped>
</style>