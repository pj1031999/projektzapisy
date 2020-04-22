<script lang="ts">
import Vue from "vue";
import Component from "vue-class-component";

@Component({
  props: {
    label: String,
    type: String,
    capacity: Number
  }
})
export default class ClassroomField extends Vue {}
</script>


<template>
  <div class="p-3 text-center">
    {{ label }}
    <div class="container p-0 m-0">
      <div class="row">
        <div class="col-sm-2 p-1">
          <button type="button" class="btn btn-primary">Wybierz</button>
        </div>
        <div class="col-sm-8 p-1">
          <div class="container p-0 m-0">
            <div class="row">
              <div class="col">
                <div style="height: 35px">
                  <div class="progress" style="height: 35px">
                    <div class="progress-bar bg-light" role="progressbar" style="width: 14.28%"></div>
                    <div
                      class="progress-bar bg-secondary progress-bar-striped"
                      role="progressbar"
                      style="width: 14.28%"
                    >Zajęte</div>
                    <div class="progress-bar bg-light" role="progressbar" style="width: 32.14%"></div>
                    <div
                      class="progress-bar bg-secondary progress-bar-striped"
                      role="progressbar"
                      style="width: 17.85%"
                    >Zajęte</div>
                    <div class="progress-bar bg-light" role="progressbar" style="width: 21.42%"></div>
                  </div>
                  <div
                    style="z-index: 2; position: relative; top: -35px; opacity: 0.5; width: 100%"
                  >
                    <div class="progress bg-transparent" style="height: 35px">
                      <div
                        class="progress-bar bg-transparent"
                        role="progressbar"
                        style="width: 25%;"
                      ></div>
                      <div class="progress-bar bg-primary" role="progressbar" style="width: 21.42%"></div>
                      <div
                        class="progress-bar bg-transparent"
                        role="progressbar"
                        style="width: 53.58%;"
                      ></div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
            <div class="row" style="font-family:monospace; position: relative">
              <div class="d-flex flex-row justify-content-between" style="width: 100%">
                <div>08:00</div>
                <div>10:00</div>
                <div>12:00</div>
                <div>14:00</div>
                <div>16:00</div>
                <div>18:00</div>
                <div>20:00</div>
                <div>22:00</div>
              </div>
            </div>
          </div>
        </div>
        <div class="col-sm-2 p-1">{{ type }}, pojemność: {{ capacity }}</div>
      </div>
    </div>
  </div>
</template>