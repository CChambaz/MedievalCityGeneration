import numpy as np
import matplotlib
import matplotlib.pyplot as plt

def GenerateBarChart(labels, dataLabel, data, chartTitle, chartYLabel, barWidth=0.35):
    npArray = np.arange(len(labels))

    fig, ax = plt.subplots()

    rects = []

    dataHalfSize = len(data) / 2
    dataHalfSize *= -1

    for i in range(len(data)):
        rects.append(ax.bar(npArray + i * barWidth, data[i], width=barWidth, label=dataLabel[i]))

    ax.set_ylabel(chartYLabel)
    ax.set_title(chartTitle)
    ax.set_xticks(npArray + barWidth + barWidth / 2)
    ax.set_xticklabels(labels)
    ax.legend()

    for container in rects:
        for rect in container.patches:
            height = rect.get_height()

            ax.annotate('{}'.format(height),
                    xy=(rect.get_x() + barWidth / 2, height),
                    xytext=(0, 3),  # 3 points vertical offset
                    textcoords="offset points",
                    ha='center', va='bottom')

    fig.tight_layout()

    plt.show()
