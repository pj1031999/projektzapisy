<script lang="ts">
import Vue from "vue";
import { mapGetters } from "vuex";
import { ThesisInfo } from "../store/theses";

import Component from "vue-class-component";
@Component({
  computed: {
    ...mapGetters("theses", {
      theses: "theses"
    }),
    ...mapGetters("filters", {
      tester: "visible"
    })
  }
})
export default class ThesesList extends Vue {
  // The list should be initialised to contain all the theses and then apply
  // filters whenever they update.
  visibleTheses: ThesisInfo[] = [];

  created() {
    this.$store.dispatch("theses/initFromJSONTag");
  }

  mounted() {
    this.visibleTheses = this.theses;

    console.log(this.theses);

    this.$store.subscribe((mutation, state) => {
      switch (mutation.type) {
        case "filters/registerFilter":
          this.visibleTheses = this.theses.filter(this.tester);
          break;
      }
    });
  }

  row_click(url) {
    window.location.href = url;
  }
}
</script>

<template>
  <div>
    <table class="table table-hover">
      <thead style="text-align: center">
        <tr>
          <th style="width: 5%">Rezerwacja</th>
          <th style="width: 65%">Tytuł</th>
          <th style="width: 10%">Typ</th>
          <th style="width: 20%">Promotor</th>
        </tr>
      </thead>
      <tbody style="text-align: center">
        <tr
          v-for="t of visibleTheses"
          :key="t.id"
          style="cursor: pointer"
          v-on:click="row_click(t.url)"
        >
          <td>
            <div class="form-check">
              <input
                type="checkbox"
                class="form-check-input"
                disabled
                v-bind:checked="!t.is_available"
              />
            </div>
          </td>
          <td style="text-align: left">
            {{ t.title }}
            <em v-if="!t.has_been_accepted" class="text-muted">({{ t.status }})</em>
          </td>
          <td>{{ t.kind }}</td>
          <td>{{ t.advisor }}</td>
        </tr>
      </tbody>
    </table>
    <div v-if="!visibleTheses.length" class="text-center">
      <em class="text-muted">Brak prac dyplomowych.</em>
    </div>
  </div>
</template>