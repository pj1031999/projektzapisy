<script lang="ts">
import Vue from "vue";
import { mapGetters } from "vuex";
import { ThesisInfo } from "../store/theses";
import SorterField from "./sorters/SorterField.vue";
import CheckFilter from "./filters/CheckFilter.vue";
import Component from "vue-class-component";

@Component({
  components: {
    SorterField
  },
  computed: {
    ...mapGetters("theses", {
      theses: "theses"
    }),
    ...mapGetters("filters", {
      tester: "visible"
    }),
    ...mapGetters("sorting", {
      compare: "compare",
      isEmpty: "isEmpty"
    })
  }
})
export default class ThesesList extends Vue {
  // The list should be initialised to contain all the theses and then apply
  // filters and sorting whenever they update.
  visibleTheses: ThesisInfo[] = [];

  created() {
    this.$store.dispatch("theses/initFromJSONTag");
  }

  mounted() {
    this.visibleTheses = this.theses;
    this.visibleTheses = this.theses.sort(this.compare);

    this.$store.subscribe((mutation, state) => {
      switch (mutation.type) {
        case "filters/registerFilter":
          this.visibleTheses = this.theses.filter(this.tester);
          this.visibleTheses.sort(this.compare);
          break;
        case "sorting/changeSorting":
          this.visibleTheses = this.theses.filter(this.tester);
          this.visibleTheses.sort(this.compare);
          break;
      }
    });
  }
}
</script>

<style scoped>
#theses-list {
  display: block;
  width: 100%;
  text-align: center;
  -webkit-user-select: none;
  -moz-user-select: none;
  -ms-user-select: none;
  user-select: none;
}
#list-header {
  font-weight: bold;
}
.is-available-col {
  width: 10%;
}

.title-col {
  width: 55%;
}

.kind-col {
  width: 15%;
}

.advisor-col {
  width: 20%;
}

.list-row-out:link {
  text-decoration: none;
  color: black;
}

/* visited link */
.list-row-out:visited {
  color: black;
}

/* mouse over link */
.list-row-out:hover {
  color: black;
  background-color: gray;
}

/* selected link */
.list-row-out:active {
  color: black;
}

.list-row-in {
  display: block;
  border-top: 1px solid #dee2e6;
}

.list-row-in:hover {
  background-color: rgb(236, 236, 236);
}
</style>

<template>
  <div>
    <div id="theses-list">
      <div id="list-header" class="p-2 d-flex flex-row">
        <div class="p-2 is-available-col">Rezerwacja</div>
        <SorterField class="p-2 title-col" property="title" label="Tytuł" />
        <SorterField class="p-2 kind-col" property="kind" label="Typ" />
        <SorterField class="p-2 advisor-col" property="advisor" label="Promotor" />
      </div>
      <div id="list-body">
        <a class="list-row-out" v-for="t of visibleTheses" :key="t.id" :href="t.url">
          <div class="p-2 d-flex flex-row list-row-in">
            <div class="p-2 is-available-col">
              <div class="form-check">
                <input
                  type="checkbox"
                  class="form-check-input"
                  disabled
                  v-bind:checked="!t.is_available"
                />
              </div>
            </div>
            <div class="p-2 title-col text-left">
              {{ t.title }}
              <em v-if="!t.has_been_accepted" class="text-muted">({{ t.status }})</em>
            </div>
            <div class="p-2 kind-col">{{ t.kind }}</div>
            <div class="p-2 advisor-col">{{ t.advisor }}</div>
          </div>
        </a>
      </div>
    </div>
    <div v-if="!visibleTheses.length" class="text-center">
      <em class="text-muted">Brak prac dyplomowych.</em>
    </div>
  </div>
</template>