<template>
    <table class='temps'>
        <tr v-for="(row, row_index) in city_temps" :key="row_index">
            <td class='city_name'>{{ row.city.name }}</td>
            <td :style="getStyle(avg_temp)" class='temp' v-for="(avg_temp, index) in row.temps" :key="index">
                {{ avg_temp }}
            </td>
        </tr>
    </table>
</template>

<script>
/*
 * taken from wikipedia WeatherBox
 * https://en.wikipedia.org/wiki/Template:Weather_box/colt
*/
let colors = [
    ['#4444FF', '#FFFFFF'],
    ['#4A4AFF', '#FFFFFF'],
    ['#4F4FFF', '#FFFFFF'],
    ['#5555FF', '#FFFFFF'],
    ['#5A5AFF', '#FFFFFF'],
    ['#5F5FFF', '#FFFFFF'],
    ['#6565FF', '#FFFFFF'],
    ['#6A6AFF'],
    ['#7070FF'],
    ['#7575FF'],
    ['#7A7AFF'],
    ['#8080FF'],
    ['#8585FF'],
    ['#8B8BFF'],
    ['#9090FF'],
    ['#9595FF'],
    ['#9B9BFF'],
    ['#A0A0FF'],
    ['#A6A6FF'],
    ['#ABABFF'],
    ['#B0B0FF'],
    ['#B6B6FF'],
    ['#BBBBFF'],
    ['#C1C1FF'],
    ['#C6C6FF'],
    ['#CBCBFF'],
    ['#D1D1FF'],
    ['#D6D6FF'],
    ['#DCDCFF'],
    ['#E1E1FF'],
    ['#E6E6FF'],
    ['#ECECFF'],
    ['#F1F1FF'],
    ['#F7F7FF'],
    ['#FCFCFF'],
    ['#FFFBF8'],
    ['#FFF4EA'],
    ['#FFEDDC'],
    ['#FFE6CE'],
    ['#FFDFC0'],
    ['#FFD9B3'],
    ['#FFD2A5'],
    ['#FFCB97'],
    ['#FFC489'],
    ['#FFBD7C'],
    ['#FFB66E'],
    ['#FFAF60'],
    ['#FFA852'],
    ['#FFA144'],
    ['#FF9B37'],
    ['#FF9429'],
    ['#FF8D1B'],
    ['#FF860D'],
    ['#FF7F00'],
    ['#FF7800'],
    ['#FF7100'],
    ['#FF6A00'],
    ['#FF6300'],
    ['#FF5D00'],
    ['#FF5600'],
    ['#FF4F00'],
    ['#FF4800'],
    ['#FF4100'],
    ['#FF3A00'],
    ['#FF3300'],
    ['#FF2C00'],
    ['#FF2500'],
    ['#FF1F00'],
    ['#FF1800', '#FFFFFF'],
    ['#FF1100', '#FFFFFF'],
    ['#FF0A00', '#FFFFFF'],
    ['#FF0300', '#FFFFFF'],
    ['#F80000', '#FFFFFF'],
    ['#EA0000', '#FFFFFF'],
    ['#DC0000', '#FFFFFF'],
    ['#CE0000', '#FFFFFF'],
    ['#C00000', '#FFFFFF'],
    ['#B30000', '#FFFFFF'],
    ['#A50000', '#FFFFFF'],
    ['#970000', '#FFFFFF'],
    ['#890000', '#FFFFFF'],
    ['#7C0000', '#FFFFFF'],
    ['#6E0000', '#FFFFFF'],
    ['#600000', '#FFFFFF'],
    ['#520000', '#FFFFFF'],
    ['#440000', '#FFFFFF'],
    ['#370000', '#FFFFFF'],
    ['#290000', '#FFFFFF'],
    ['#1B0000', '#FFFFFF'],
    ['#0D0000', '#FFFFFF'],
];
let minColorTemp = -30;


import json from "@/assets/temps.json";

export default {
  name: 'Temps',
  data: function() {
    return {
      city_temps: json,
      getStyle: temp => {
        let index = Math.trunc(temp) - minColorTemp;
        if (index > colors.length - 1)
            index = colors.length - 1;
        if (index < 0)
            index = 0;
        let colorRow = colors[index];

        let styles = `background:${colorRow[0]}`;
        if (colorRow.length > 1)
            styles += `;color:${colorRow[1]}`;

        return styles;
      }
    }; 
  }
}
</script>


<style scoped>
    .temps {
        margin-left: auto;
        margin-right: auto;
        border-collapse: collapse;
    }
    .temps td {
        padding: 0.2em;
        border: 1px solid #a0a0a0;
    }
    .city_name { text-align: left; }
    .temp { text-align: center; }
</style>