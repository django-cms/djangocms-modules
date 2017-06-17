/*!
 * @author:    Divio AG
 * @copyright: http://www.divio.ch
 */

'use strict';

// #####################################################################################################################
// #IMPORTS#
var gulp = require('gulp');
var gutil = require('gulp-util');
var jshint = require('gulp-jshint');
var jscs = require('gulp-jscs');

// #####################################################################################################################
// #SETTINGS#
var paths = {
    'js': './aldryn_blueprint/static/aldryn_blueprint/js/'
};

var patterns = {
    'js': [
        paths.js + '*.js',
        paths.js + '**/*.js',
        paths.js + '**/**/*.js',
        '!' + paths.js + '*.min.js',
        '!' + paths.js + '**/*.min.js'
    ]
};
patterns.jshint = patterns.js.concat(['!' + paths.js + 'libs/*.js', './gulpfile.js']);


// #####################################################################################################################
// #LINTING#
gulp.task('lint', function () {
    gulp.src(patterns.jshint)
        .pipe(jshint())
        .pipe(jscs())
        .on('error', function (error) {
            gutil.log('\n' + error.message);
        })
        .pipe(jshint.reporter('jshint-stylish'));
});


// #####################################################################################################################
// #COMMANDS#
gulp.task('watch', function () {
    gulp.watch(patterns.jshint, ['lint']);
});

gulp.task('default', ['lint']);
