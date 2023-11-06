

document.getElementById('course_name').addEventListener('change', function () {
    let courseId = this.value;
    if (courseId) {
        document.getElementById('loading-indicator').style.display = 'block';
        fetch('/layouts_for_course/' + courseId)
            .then(response => {
                if (!response.ok) {
                    throw new Error('Network response was not ok');
                }
                return response.json();
            })
            .then(data => {
                let layoutSelect = document.getElementById('layout_name');
                layoutSelect.innerHTML = '<option value="" disabled selected>Select a Layout</option>';
                for (let layout of data) {
                    let option = document.createElement('option');
                    option.text = layout;
                    layoutSelect.add(option);
                }
                if (data.length > 0) {
                    layoutSelect.selectedIndex = 1;
                }
                document.getElementById('loading-indicator').style.display = 'none';
            })
            .catch(error => {
                console.error('There has been a problem with your fetch operation:', error);
            });
    }
});

document.getElementById('player_name').addEventListener('change', function () {
    let playerId = this.value;
    if (playerId) {
        document.getElementById('loading-indicator').style.display = 'block';
        fetch('/courses_for_player/' + playerId)
            .then(response => {
                if (!response.ok) {
                    throw new Error('Network response was not ok');
                }
                return response.json();
            })
            .then(data => {
                let courseSelect = document.getElementById('course_name');
                courseSelect.innerHTML = '<option value="" disabled selected>Select a Course</option>';
                for (let course of data) {
                    let option = document.createElement('option');
                    option.text = course;
                    courseSelect.add(option);
                }
                if (data.length > 0) {
                    courseSelect.selectedIndex = 1;
                }
                document.getElementById('layout_name').innerHTML = '<option value="" disabled selected>Select a Layout</option>';
                document.getElementById('loading-indicator').style.display = 'none';
            })
            .catch(error => {
                console.error('There has been a problem with your fetch operation:', error);
            });
    }
});
document.getElementById('scorecard-form').addEventListener('submit', function (event) {
    event.preventDefault();

    let playerName = document.getElementById('player_name').value;
    let courseName = document.getElementById('course_name').value;
    let layoutName = document.getElementById('layout_name').value;

    document.getElementById('loading-indicator').style.display = 'block';

    fetch('/scorecard_data/' + playerName + '/' + courseName + '/' + layoutName)
        .then(response => {
            if (!response.ok) {
                throw new Error('Network response was not ok');
            }
            return response.json();
        })
        .then(data => {
            let numResults = document.getElementById('num-results').value;

            // If the user selected "All", set numResults to the length of the data array
                if (numResults === 'all') {
                    numResults = data.length;
                }

            // Limit the data to the first numResults scorecards
            data = data.slice(0, numResults);
                let resultsDiv = document.getElementById('results');
                resultsDiv.innerHTML = ''; // Clear the previous results

            // Create a table
            let table = document.createElement('table');
            table.classList.add('results-table');

            // Create the table headers
            let thead = document.createElement('thead');
            thead.innerHTML = `
                <tr>
                    <th>Player</th>
                    <th>Course</th>
                    <th>Layout</th>
                    <th>Total Score</th>
                    <th>+/-</th>
                </tr>
            `;
            table.appendChild(thead);

            // Create a table body
            let tbody = document.createElement('tbody');
            table.appendChild(tbody);
            
            // Add the scorecards to the table
            // sort by score difference
            data.sort(function(a, b) {
                return a.score_difference - b.score_difference;
            });
            data.forEach(scorecard => {
                // Create a row for the scorecard
                let tr = document.createElement('tr');

                // Create the score_difference cell
                let scoreDifferenceCell = document.createElement('td');
                scoreDifferenceCell.textContent = scorecard.score_difference;

                // If the score_difference is negative, add the 'negative' class to the cell
                if (scorecard.score_difference < 0) {
                    scoreDifferenceCell.classList.add('negative');
                }

                // Create other cells
                let playerNameCell = document.createElement('td');
                playerNameCell.textContent = scorecard.player_name;

                let courseNameCell = document.createElement('td');
                courseNameCell.textContent = scorecard.course_name;

                let layoutNameCell = document.createElement('td');
                layoutNameCell.textContent = scorecard.layout_name;

                let totalScoreCell = document.createElement('td');
                totalScoreCell.textContent = scorecard.total_score;

                // Append the cells to the row
                tr.appendChild(playerNameCell);
                tr.appendChild(courseNameCell);
                tr.appendChild(layoutNameCell);
                tr.appendChild(totalScoreCell);
                tr.appendChild(scoreDifferenceCell);

                // Append the row to the table body
                tbody.appendChild(tr);
            });

            // Append the table to the results div
            resultsDiv.appendChild(table);

            document.getElementById('loading-indicator').style.display = 'none';
        })
        .catch(error => {
            console.error('There has been a problem with your fetch operation:', error);
        });
});
function getScoreClass(score, par) {
    if (score === 1) {
        return 'hole-in-one';
    }

    let difference = par - score;
    switch (difference) {
        case -3:
            return 'albatross';
        case -2:
            return 'eagle';
        case -1:
            return 'birdie';
        case 0:
            return 'par';
        case 1:
            return 'bogey';
        case 2:
            return 'double-bogey';
        case 3:
            return 'triple-bogey';
        default:
            return 'quatro-bogey';
    }
}