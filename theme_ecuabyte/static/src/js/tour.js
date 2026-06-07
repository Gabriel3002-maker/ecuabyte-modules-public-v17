/** @odoo-module */

import wTourUtils from '@website/js/tours/tour_utils';

const snippets = [
    { id: 's_cover', name: 'Cover' },
    { id: 's_text_image', name: 'Text - Image' },
    { id: 's_features', name: 'Features' },
];

wTourUtils.registerThemeHomepageTour("ecuabyte_tour", () => [
    wTourUtils.assertCssVariable('--color-palettes-name', '"ecuabyte-1"'),
    wTourUtils.dragNDrop(snippets[0]),
    wTourUtils.clickOnText(snippets[0], 'h1'),
    wTourUtils.goBackToBlocks(),
    wTourUtils.dragNDrop(snippets[1]),
    wTourUtils.dragNDrop(snippets[2]),
]);
