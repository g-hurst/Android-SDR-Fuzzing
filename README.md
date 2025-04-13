# WiFi Fuzzing Platform

The **WiFi Fuzzing Platform** is an advanced security research tool designed to identify vulnerabilities in the WiFi stack of Android devices. By injecting and monitoring custom-crafted network traffic, this tool enables researchers to analyze how mobile devices respond under fuzzing conditions, potentially revealing exploitable weaknesses in real-world deployments.

## What It Does

This platform:
- Parses user configuration files and automatically sets parameters for fuzzing and testing
- Offers an interactive CLI for live testing, as well as a background mode for automated fuzzing campaigns.
- Sends fuzzed network packets to Android devices using a shared WiFi based connectivity.
- Monitors the Android device’s reactions and collects behavioral logs.
- Provides packet history through collected logs for future offline analysis.

## Why Use This?

Modern Android devices are complex systems with numerous wireless communication layers. This platform aids in uncovering zero-day vulnerabilities in WiFi processing components. It enables reproducible fuzzing experiments for academic or industrial research, and provides an extensible foundation for custom protocol testing and log analysis.

## User Manual

For more information on installation, running of the application, or troublehooting, please refer to our user manual provided by the following link:

[https://g-hurst.github.io/Android-SDR-Fuzzing/](https://g-hurst.github.io/Android-SDR-Fuzzing/)

## Contributionors

This project is the resulting effort of three Purdue University Computer Engineering seniors as part of their senior capstone and is maintained by the same three:
- @g-hurst
- @rbejerano-3
- @misra22