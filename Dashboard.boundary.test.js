import { describe, it, expect, vi, beforeEach } from 'vitest'
import { mount } from '@vue/test-utils'
import Dashboard from '../src/components/Dashboard.vue'

const { instances } = vi.hoisted(() => ({ instances: [] }))

vi.mock('../src/utils/echarts', () => {
  function init() {
    const inst = { setOption: vi.fn(), resize: vi.fn(), dispose: vi.fn() }
    instances.push(inst)
    return inst
  }
  return { default: { init, use: vi.fn() } }
})

const baseSummary = {
  focusDuration: 100,
  focusCount: 5,
  distractCount: 3,
  avgDuration: 20
}

function mountWith(props = {}) {
  return mount(Dashboard, {
    props: {
      summary: baseSummary,
      weeklyFocus: [{ date: '10-30', duration: 100 }],
      hourlyDistract: [0, 0, 1, 0, 0],
      ...props
    }
  })
}

describe('Dashboard 边界用例复现', () => {
  beforeEach(() => { instances.length = 0 })

  it('用例2: 全零数据被误判为空（应显示图表，实际显示"暂无数据"）', () => {
    const weeklyFocus = Array.from({ length: 7 }, (_, i) => ({ date: `10-${i + 25}`, duration: 0 }))
    const hourlyDistract = new Array(24).fill(0)
    const wrapper = mountWith({ weeklyFocus, hourlyDistract })

    const empties = wrapper.findAll('.empty')
    expect(empties.length).toBe(2)

    expect(instances[0].setOption).not.toHaveBeenCalled()
    expect(instances[1].setOption).not.toHaveBeenCalled()
  })

  it('用例4: 专注时长为负数（应显示0分钟，实际显示-30分钟）', () => {
    const wrapper = mountWith({ summary: { ...baseSummary, focusDuration: -30 } })
    const values = wrapper.findAll('.card-value')
    expect(values[0].text()).toBe('-30')
    expect(wrapper.findAll('.card-unit')[0].text()).toBe('分钟')
  })

  it('用例6: 分心数组长度≠24（应校验为24，实际按原长度5渲染x轴）', () => {
    const hourlyDistract = [1, 2, 3, 4, 5]
    mountWith({ hourlyDistract })

    expect(instances[1].setOption).toHaveBeenCalledTimes(1)
    const option = instances[1].setOption.mock.calls[0][0]
    expect(option.xAxis.data.length).toBe(5)
    expect(option.xAxis.data).toEqual(['0时', '1时', '2时', '3时', '4时'])
  })

  it('用例7: 分心数组含负数（应按0处理，实际传入负值-3）', () => {
    const hourlyDistract = [1, -3, 2, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
    mountWith({ hourlyDistract })

    expect(instances[1].setOption).toHaveBeenCalledTimes(1)
    const option = instances[1].setOption.mock.calls[0][0]
    const values = option.series[0].data.map(d => d.value)
    expect(values).toContain(-3)
  })
})
