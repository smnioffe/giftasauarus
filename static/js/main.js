let clickCount = 0;

function flipTiles(clickedTile) {
    const currentValues = {};
    $('.tile-content').each(function (index, tile) {
        currentValues['tile' + (index + 1)] = parseInt($(tile).text());
    });

    clickCount += 1;
    const clickedNumber = clickCount;;

    $.ajax({
        url: '/flip-tiles',
        method: 'POST',
        contentType: 'application/json',
        data: JSON.stringify({
            currentValues: currentValues,
            clickedNumber: clickedNumber
        }),
        success: function (response) {
            const newValues = response.newValues;
            const step = response.step;
            console.log(newValues)
           // if (step + 1 < GIFT_ATTRIBUTES.length) {
                // Update the card content with the new values
                $('.tile-content').each(function (index, tile) {
                    $(tile).text(newValues['tile' + (index + 1)]);
                   // const tileNumber = index + 1;
                    //$(tile).text(newValues['tile' + tileNumber]);
                });
            //} else {
                $.ajax({
                    url: '/recommendations',
                    method: 'GET',
                    success: function (response) {
                        const recommendedGifts = response.recommendedGifts;
                        console.log("Recommended gifts:", recommendedGifts);
                    }
                });
          //  }
        }
        
    });
}

$('.tile').on('click', function () {
    flipTiles(this);
});
