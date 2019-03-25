const axe = require('@ictu/axe-reports'),
      fs = require('fs');

const directory = 'test/accessibility/';

fs.readdir(directory, {}, function(error, files) {
    if (error) {
        throw error;
    }
    let newReport = true;
    files.forEach(function(filename) {
        if (filename.endsWith('.json')) {
            axe.processResults(
                JSON.parse(fs.readFileSync(directory + filename)),
                'csv', directory + 'report.txt', newReport
            );
            newReport = false;
        }
    });
});
