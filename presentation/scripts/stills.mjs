import {execFileSync} from 'node:child_process';
const durations=[14,16,20,18,20,18,18,16,10];
let from=0;
for(let i=0;i<durations.length;i++){
  execFileSync('npx',['remotion','still','src/index.tsx','JuryPitch',`out/slide-${String(i+1).padStart(2,'0')}.png`,`--frame=${from+Math.min(160,durations[i]*30-30)}`,'--browser-executable=/Applications/Google Chrome.app/Contents/MacOS/Google Chrome'],{stdio:'inherit'});
  from+=durations[i]*30;
}
