import child_process from 'child_process';
import util from 'util';

const exec = util.promisify(child_process.exec);

async function ping(hostname) {
  try {
    const {stdout, stderr} = await exec(`ping -c 3 ${hostname}`);
    console.log('stderr: ', stderr);
    console.log('stdout: ', stdout);
  } catch (err) {
    console.log(err);
  }
}

ping('www.google.com');