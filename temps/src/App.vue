<template>
  <div id="app">
    <h1>City temps</h1>
    <Temps/>
  </div>
</template>

<script>
import Temps from './components/Temps.vue'

export default {
  name: 'App',
  components: {
    Temps
  }
}
</script>

<style>
#app {
  font-family: Avenir, Helvetica, Arial, sans-serif;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
  text-align: center;
  color: #2c3e50;
  margin-top: 60px;
}
</style>
