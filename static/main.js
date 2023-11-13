window.onload = function () {
    const courseNameElement = document.getElementById("course_name");
    const layoutNameElement = document.getElementById("layout_name");
    const playerNameElement = document.getElementById("player_name");
    const loadingIndicatorElement = document.getElementById('loading-indicator');
    const scorecardFormElement = document.getElementById('scorecard-form');
    const resultsElement = document.getElementById('results');
    const numResultsElement = document.getElementById('num-results');

    if (!courseNameElement || !layoutNameElement || !playerNameElement || !loadingIndicatorElement || !scorecardFormElement || !resultsElement || !numResultsElement) {
        console.error("One or more elements not found");
        return;
    }

    const updatedEvent = new Event('updated');

    function fetchData(endpoint, selectElement, defaultOptionText) {
        // Log the URL being fetched
        console.log('Fetching URL:', endpoint);
    
        loadingIndicatorElement.style.display = 'block';
        return fetch(endpoint)
            .then(response => {
                if (!response.ok) {
                    throw new Error('Network response was not ok');
                }
                return response.json();
            })
            .then(data => {
                console.log(data);
                if (data?.length > 0) {
                    selectElement.innerHTML = `<option value="" disabled selected>${defaultOptionText}</option>`;
                    for (let item of data) {
                        let option = document.createElement('option');
                        option.text = typeof item === 'string' ? item : item.name;
                        selectElement.appendChild(option);
                    }
                    loadingIndicatorElement.style.display = 'none';
                    if (selectElement.options.length > 1) {
                        selectElement.selectedIndex = 1;
                        selectElement.dispatchEvent(updatedEvent);
                    }
                }
            })
            .catch(error => {
                console.error('There has been a problem with your fetch operation:', error);
            });
    }
    

    function updateLayouts() {
        let selectedCourseName = courseNameElement.options[courseNameElement.selectedIndex].text;
        
        // Check if a valid course name is selected
        if (selectedCourseName === 'Select a Course') {
            console.log('No valid course selected');
            return;
        }
    
        let fetchUrl = `/layouts_for_course/${encodeURIComponent(selectedCourseName)}`;
        fetchData(fetchUrl, layoutNameElement, 'Select a Layout');
    }
    

    function updatePlayers() {
        let selectedCourseName = courseNameElement.options[courseNameElement.selectedIndex].text;
        let selectedLayoutName = layoutNameElement.options[layoutNameElement.selectedIndex].text;
        let fetchUrl = `/players_for_course_and_layout/${encodeURIComponent(selectedCourseName)}/${encodeURIComponent(selectedLayoutName)}`;
        fetchData(fetchUrl, playerNameElement, 'Select a Player');
    }

    courseNameElement.addEventListener('change', () => {
        updateLayouts();
    });

    layoutNameElement.addEventListener('change', () => {
        updatePlayers();
    });

    scorecardFormElement.addEventListener('submit', (event) => {
        // ... (unchanged)
    });

    // Fetch the courses data when the page loads
    fetchData('/courses_for_all_players', courseNameElement, 'Select a Course');


    courseNameElement.addEventListener('updated', () => {
        // Fetch the layouts data when a course is selected
        let selectedCourseName = courseNameElement.options[courseNameElement.selectedIndex].text;
        let fetchUrl = `/layouts_for_course/${encodeURIComponent(selectedCourseName)}`;
        fetchData(fetchUrl, layoutNameElement, 'Select a Layout');
    });

    layoutNameElement.addEventListener('updated', () => {
        // Fetch the players data when a layout is selected
        let selectedCourseName = courseNameElement.options[courseNameElement.selectedIndex].text;
        let selectedLayoutName = layoutNameElement.options[layoutNameElement.selectedIndex].text;
        let fetchUrl = `/players_for_course_and_layout/${encodeURIComponent(selectedCourseName)}/${encodeURIComponent(selectedLayoutName)}`;
        console.log('Layouts fetch URL:', fetchUrl); // Added for debugging
        fetchData(fetchUrl, playerNameElement, 'Select a Player');
    });

    scorecardFormElement.addEventListener('submit', (event) => {
        event.preventDefault();

        let selectedCourseName = courseNameElement.options[courseNameElement.selectedIndex].text;
        let selectedLayoutName = layoutNameElement.options[layoutNameElement.selectedIndex].text;
        let selectedPlayerName = playerNameElement.options[playerNameElement.selectedIndex].text;
        let numResults = numResultsElement.value;
        let fetchUrl = `/scorecard_data/${encodeURIComponent(selectedPlayerName)}/${encodeURIComponent(selectedCourseName)}/${encodeURIComponent(selectedLayoutName)}/${encodeURIComponent(numResults)}`;

        document.getElementById('loading-indicator').style.display = 'block';
        console.log('Fetching scorecard data...');
        fetch(fetchUrl)
            .then(response => {
                console.log('Fetch response:', response);
                if (!response.ok) {
                    throw new Error('Network response was not ok');
                }
                return response.json();
            })
            .then(data => {
                console.log('Processing data:', data);

                if (numResults === 'all') {
                    numResults = data.length;
                }
                data.sort((a, b) => a.total_score - b.total_score);
                data = data.slice(0, numResults);
                let resultsDiv = document.getElementById('results');
                resultsDiv.innerHTML = '';

                let table = document.createElement('table');
                table.id = 'scorecard-table';

                let thead = document.createElement('thead');
                let headerRow = document.createElement('tr');
                ['Player Name', 'Course Name', 'Layout', 'Total Score', '+/-', 'Date'].forEach(headerText => {
                    let th = document.createElement('th');
                    th.textContent = headerText;
                    headerRow.appendChild(th);
                });
                thead.appendChild(headerRow);
                table.appendChild(thead);

                let tbody = document.createElement('tbody');
                table.appendChild(tbody);

                data.sort((a, b) => a.score_difference - b.score_difference);
                data.forEach(scorecard => {
                    let tr = document.createElement('tr');
                    let dateCell = document.createElement('td');
                    dateCell.textContent = scorecard.date;
                    tr.appendChild(dateCell);

                    tr.addEventListener('click', function () {
                        let holeScoresTr = tr.nextElementSibling;
                        if (holeScoresTr && holeScoresTr.classList.contains('hole-score')) {
                            holeScoresTr.remove();
                        } else {
                            console.log('Scorecard object:', scorecard);

                            fetch('/hole_scores/' + scorecard.id)  // Use the scorecard_id directly
                                .then(response => {
                                    if (!response.ok) {
                                        throw new Error('Network response was not ok');
                                    }
                                    return response.json();
                                })
                                .then(holeScores => {
                                    console.log(holeScores);

                                    holeScoresTr = document.createElement('tr');
                                    holeScoresTr.classList.add('hole-score');
                                    holeScores.sort((a, b) => a.hole_number - b.hole_number);

                                    holeScores.forEach(holeScore => {
                                        let td = document.createElement('td');
                                        td.textContent = holeScore.strokes;
                                        let className = getScoreClass(holeScore.strokes, holeScore.par);  // Moved inside the forEach block
                                        td.className = 'hole-score ' + className;
                                        console.log(className);
                                        td.className = className;
                                        holeScoresTr.appendChild(td);
                                    });

                                    tr.parentNode.insertBefore(holeScoresTr, tr.nextSibling);
                                })
                                .catch(error => {
                                    console.error('There has been a problem with your fetch operation:', error);
                                });
                        }
                    });
                    

                    let postToTelegramButton = document.createElement('button');
                    postToTelegramButton.textContent = 'Post to Telegram';
                    postToTelegramButton.addEventListener('click', function () {
                        event.stopPropagation();
                        console.log('Scorecard object:', scorecard);

                        fetch('/postToTelegram', {
                            method: 'POST',
                            headers: {
                                'Content-Type': 'application/json'
                            },
                            body: JSON.stringify({
                                chat_id: '-4032226032',
                                text: `Scorecard:\nPlayer Name: ${scorecard.player_name}\nCourse Name: ${scorecard.course_name}\nLayout Name: ${scorecard.layout}\nTotal Score: ${scorecard.total_score}\nScore Difference: ${scorecard.score_difference}`,
                                disable_web_page_preview: true,
                                disable_notification: true
                            })
                        })
                            .then(response => {
                                if (!response.ok) {
                                    throw new Error('Network response was not ok');
                                }
                                return response.json();
                            })
                            .then(data => {
                                console.log('Message sent to Telegram:', data);
                            })
                            .catch(error => {
                                console.error('There has been a problem with your fetch operation:', error);
                            });
                    });

                    let scoreDifferenceCell = document.createElement('td');
                    scoreDifferenceCell.textContent = scorecard.score_difference;

                    if (scorecard.score_difference < 0) {
                        scoreDifferenceCell.classList.add('negative');
                    }

                    let playerNameCell = document.createElement('td');
                    playerNameCell.textContent = scorecard.player_name;

                    let courseNameCell = document.createElement('td');
                    courseNameCell.textContent = scorecard.course_name;

                    let layoutNameCell = document.createElement('td');
                    layoutNameCell.textContent = scorecard.layout_name;

                    let totalScoreCell = document.createElement('td');
                    totalScoreCell.textContent = scorecard.total_score;

                    tr.appendChild(playerNameCell);
                    tr.appendChild(courseNameCell);
                    tr.appendChild(layoutNameCell);
                    tr.appendChild(totalScoreCell);
                    tr.appendChild(scoreDifferenceCell);
                    tr.appendChild(dateCell);
                    tr.appendChild(postToTelegramButton);

                    tbody.appendChild(tr);
                });

                resultsDiv.appendChild(table);

                document.getElementById('loading-indicator').style.display = 'none';
            })
            .catch(error => {
                console.error('There has been a problem with your fetch operation:', error);
            });

    });
}


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
